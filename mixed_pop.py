# - Importing the relevant modules - #
import touchsim as ts
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import pandas as pd

print(f"\n==========================================")
print(f" RUNNING SIMULATION")
print(f"==========================================")
np.random.seed(42)

# - Defining Count Spikes Function - #
# Extrapolates a simple rate code from an afferent response to either noise or stimulus
def count_spikes(response):
    return sum(len(sp) for sp in response.spikes)

# - Setting Trial Parameters - #
# These parameters are set to imitate the experimental setup of the corresponding in vivo design
stimulus_frequencies = [30, 80, 130, 180, 230, 250]
band_pass = [0.1, 500]
stimulus_radius = 4 
trial_duration = 0.5
ramp_duration = 0.2
sample_rate = 5000

# - Creating a Mixed Afferent Population in the distal digit tip - #
a = ts.affpop_hand(region='D2d')

# - Population Signal Detection Threshold - #
# An algorithm has been implemented to detect the minimum amplitude of stimulus indentation to cause spiking activity per frequency condition #

# The mean of a subthreshold + suprathreshold signal is applied to the afferent population and the spike count is retrieved
# This is compared to a fixed number of spikes that was determined to be the threshold for signal detection
# The minimum and maximum amplitudes are iteratively adjusted until the differential between the two is incredibly small
# The threshold value is determined to be the average of the maximum and minimum amplitudes

threshold_search_trials = 100 #Moderate amount of trials is needed to remove any significant variance
spike_count_threshold = 20 # It was assumed that 20 spikes over .5 seconds would be a sufficient measure of detection within a population
thresholds = {}

print("Calculating Biological Population Thresholds...")
for frequency in stimulus_frequencies:
    min_amp, max_amp = 0.0000001, 1.0
    tolerance = 0.000001 
    while (max_amp - min_amp) > tolerance:
        middle = (max_amp + min_amp) / 2
        stim_trial_spikes = []
        s = ts.stim_sine(freq=frequency, amp=middle, pin_radius=stimulus_radius, 
                len=trial_duration, ramp_len=ramp_duration)
        for trials in range(threshold_search_trials):
            r = a.response(s)
            stim_trial_spikes.append(count_spikes(r))
        if np.mean(stim_trial_spikes) >= spike_count_threshold:
            max_amp = middle
        else:
            min_amp = middle
    thresholds[frequency] = max_amp
    print(f"  {frequency:3d} Hz Threshold: {max_amp:.6f} mm")

# - Noise Detection Threshold - #
# Same process as for the stimulus detection thresholds, but for the applied noise
# Only 1 threshold is needed for this, as opposed to one per frequency condition

print("\nCalculating Noise Baseline")
min_amp, max_amp = 0.0000001, 100
while (max_amp - min_amp) > 0.000001:
    middle = (max_amp + min_amp) / 2
    noise_trial_spikes = []
    for trials in range(threshold_search_trials):
        noise_stim = ts.stim_noise(
            amp = middle, 
            freq = band_pass, # Bandpassed from 0.1 to 500 as this falls in the frequency range of low threshold afferent fibre detection
            pin_radius = stimulus_radius, len = trial_duration, ramp_len = ramp_duration
            )
        r = a.response(noise_stim)
        noise_trial_spikes.append(count_spikes(r))
    if np.mean(noise_trial_spikes) >= spike_count_threshold:
        max_amp = middle
    else:
        min_amp = middle       
noise_base = max_amp
print(f" Noise Baseline: {max_amp:.6f} mm")

# - Simulation Paradigm - #
# The Simulation Paradigm follows a 2AFC experimental design
# Using the thresholds that were gathered previously, the input signal is set to subthreshold value (currently 70%)
# An ideal observer faces two tasks {signal + noise; noise}. If the total number of spikes equals or passes the fixed detection threshold.
# It is considered a hit or a false alarm - depending on the trial
# From this, the hit rate and false alarm rate are calcualted alongside the d' value (higher d' means higher sensitivity) and the percentage of correct responses
# This process occurs for all noise x frequency conditions
# NOTE: Hautus correction is applied to account for extreme Hit or FA values (0 or 1)

sig_ratios = 0.7 # Sub-threshold signals at 70% of absolute threshold
n_trials = 1000 # Set to 1000 Monte Carlo trials to eliminate variance
noise_multipliers = [0, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0] # Focus is on intermediate levels of noise to capture stochastic resonance clearly
accuracy_results = {}
d_prime_results = {}
optimal_noise = {}
best_accuracy = {}

print("\nStarting Population-Coded Simulation...\n")
for frequency in stimulus_frequencies:
    sig_amp = thresholds[frequency] * sig_ratios
    target_threshold = spike_count_threshold
    optimal_noise[frequency] = None # Improved visualisation of optimal noise intensity window
    best_accuracy[frequency] = 0
    # Stimulus is generated outside of loop to avoid extra computational cost - amplitude set to below what would pass threshold
    stim_sig = ts.stim_sine(amp = sig_amp, freq = frequency, 
                            pin_radius = stimulus_radius, 
                            len = trial_duration, ramp_len = ramp_duration
                            ) 
    for mult in noise_multipliers:
        noise_amp = noise_base * mult
        hits = 0
        false_alarms = 0
        for trial in range(n_trials):
            # Building noise stimulus for the signal + noise trial
            if noise_amp > 0:
                noise_stim_sn = ts.stim_noise(amp = noise_amp, freq= band_pass, 
                                            pin_radius = stimulus_radius, 
                                            len = trial_duration, ramp_len = ramp_duration
                                            )
                noise_trace_sn = noise_stim_sn.trace # Extracting the amplitude values over the course of the trial duration to allow noise to be applied to stimulus
            else:
                noise_trace_sn = np.zeros(int(trial_duration * sample_rate))
            
            # - Signal + Noise Trial (Hits) - #
            comb_stim = ts.Stimulus(trace = stim_sig.trace + noise_trace_sn, 
                                    location = stim_sig.location, 
                                    pin_radius = stimulus_radius, fs = sample_rate
                                    )
            if count_spikes(a.response(comb_stim)) >= target_threshold:
                hits += 1
            # Separate noise stimuli is generated for noise trial because it is desirable to have two sets of applied noise - follows in vivo procedure
            if noise_amp > 0:
                noise_stim_n = ts.stim_noise(amp = noise_amp, freq = band_pass, 
                                            pin_radius = stimulus_radius, 
                                            len = trial_duration, ramp_len = ramp_duration)
                noise_trace_n = noise_stim_n.trace
            else:
                noise_trace_n = np.zeros(int(trial_duration * sample_rate))

            # - Noise Only Trial (False Alarms) - #
            blank_stim = ts.Stimulus(trace = noise_trace_n, location = stim_sig.location, 
                                    pin_radius = stimulus_radius, fs = sample_rate)
            if count_spikes(a.response(blank_stim)) >= target_threshold:
                false_alarms += 1
        
        # Calculating hit rates and false alarm rates in order to calculate detection accuracy - Hautus correction applied
        hit_rate = (hits + 0.5) / (n_trials + 1)
        fa_rate = (false_alarms + 0.5) / (n_trials + 1)
        # Z values are calculated to find d'
        z_hit = stats.norm.ppf(hit_rate)
        z_fa = stats.norm.ppf(fa_rate)
        d_prime = z_hit - z_fa
        # Pecentage of correct decisions
        p_correct = ((hit_rate + (1.0 - fa_rate)) / 2.0) * 100
        # Calculating Confidence Intervals
        se_hit = np.sqrt(hit_rate * (1 - hit_rate) / n_trials)
        se_fa = np.sqrt(fa_rate * (1 - fa_rate) / n_trials)
        se_p = 0.5 * np.sqrt(se_hit**2 + se_fa**2) * 100
        ci_lower = max(0, p_correct - 1.96 * se_p)
        ci_upper = min(100, p_correct + 1.96 * se_p)
        # Calculating the highest chance of detection as well as what noise multiplier is applied
        if p_correct > best_accuracy[frequency]:
            best_accuracy[frequency] = p_correct
            optimal_noise[frequency] = mult
        # Storing accuracy and d' results for statistical analysis
        accuracy_results[(frequency, mult)] = p_correct
        d_prime_results[(frequency, mult)] = d_prime

        print(f"{mult:<4} mult | {frequency:3d} Hz | HR: {hit_rate:.2f} | FAR: {fa_rate:.2f} | d': {d_prime:.2f} | Acc: {p_correct:.1f}%")

    print("Simulation Complete!")