An in silico Yes-No experiment to showcase the influence of the stochastic resonance effect on tactile sensitivity within TouchSim, which models the glabrous skin of the hand (hsaal/touchsim on GitHub).

Stochastic resonance is when an intermediate level of noise, when superimposed onto a subthreshold stimulus, improves signal detection. I demonstrate that this effect can be observed in Python, and I investigated how the effect manifests under different conditions.

A binary search algorithm is used to estimate the minimum amplitude required to elicit an arbitrary spike count that is considered to mean the stimulus has been detected. This is found for both noise and a sinusoidal stimulus. After finding these values, a Yes-No experiment is simulated.

The signal is set to 70% of the minimum signal amplitude to guarantee that stimuli are not instantly detected. An observer then undergoes 2 conditions: (1) a noise only condition (2) a signal + noise condition, whereby a noise multiplier is superimposed onto the subthreshold signal. A hit is registered when (in the S+N condition) the signal is detected by the observer - when spiking behaviour is above the set detection count. For the nosie condition, this would register a false alarm. This was conducted across various noise multipliers to find the optimal noise multiplier to enhance tactile sensitivity.

After n trials, d' (a measure of sensitivity) is calculated from the z values of both the hit/alarm rates. A higher d' means that the S+N condition was more likely to be detected by the observer as opposed to the noise condition.
