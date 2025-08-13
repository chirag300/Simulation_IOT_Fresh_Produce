"""
Synthetic IoT temperature model for the trailer.

This module defines a DiurnalWithDoor class that simulates temperature
inside a refrigerated trailer.  The model includes diurnal ambient
variation, cooling toward a setpoint while doors are closed, drift toward
ambient when doors are open, random noise, and occasional heat bumps to
approximate traffic or solar load.  It exposes methods for updating the
temperature each minute and applying a spike when the doors open.
"""
import math
import random


class DiurnalWithDoor:
    """
    Synthetic IoT temperature model.

    Attributes
    ----------
    setpoint : float
        The target temperature in degrees Celsius.  When the doors are
        closed the trailer cools toward this temperature.
    cool_rate : float
        Relaxation coefficient per minute toward the setpoint when the
        doors are closed.
    drift : float
        Relaxation coefficient per minute toward ambient temperature when
        the doors are open.
    open_spike : float
        Instant temperature increase applied when the doors are opened.
    noise_sigma : float
        Standard deviation of Gaussian noise added to the trailer
        temperature each minute to simulate sensor noise and compressor
        cycling.
    traffic_bump_prob : float
        Probability each minute that an additional random warm bump will
        occur.  This models transient heat load from traffic or sun.
    traffic_bump_mag : tuple[float,float]
        Range of the uniform random warm bump, in degrees Celsius.

    Notes
    -----
    The temperature is stored in the `temp` attribute.  Call `tick_closed()`
    or `tick_open()` once per minute depending on whether the doors are
    closed or open.  To model the effect of opening the doors for a
    delivery, call `bump_on_open()` immediately before servicing begins.
    """

    def __init__(
        self,
        setpoint: float = 4.0,
        cool_rate: float = 0.15,
        drift: float = 0.02,
        open_spike: float = 1.8,
        noise_sigma: float = 0.06,
        traffic_bump_prob: float = 0.02,
        traffic_bump_mag: tuple = (0.2, 0.5),
    ) -> None:
        self.setpoint = setpoint
        self.cool_rate = cool_rate
        self.drift = drift
        self.open_spike = open_spike
        self.noise_sigma = noise_sigma
        self.traffic_bump_prob = traffic_bump_prob
        self.traffic_bump_mag = traffic_bump_mag
        self.temp = setpoint

    def ambient(self, minute: int) -> float:
        """
        Compute ambient temperature for the given minute.  We use a
        simple sinusoid with mean 21°C and amplitude 3°C, peaking at
        midday.  The `minute` argument is the absolute simulation minute.
        """
        return 21.0 + 3.0 * math.sin(((minute / 60.0) - 6.0) / 24.0 * 2.0 * math.pi)

    def tick_closed(self) -> None:
        """
        Advance the temperature by one minute with the doors closed.
        Cooling toward the setpoint and random noise are applied.  A
        small warm bump may occur to approximate traffic or solar load.
        """
        # Relax toward setpoint
        self.temp += self.cool_rate * (self.setpoint - self.temp)
        # Gaussian noise
        self.temp += random.gauss(0.0, self.noise_sigma)
        # Occasional warm bump
        if random.random() < self.traffic_bump_prob:
            self.temp += random.uniform(*self.traffic_bump_mag)

    def tick_open(self, ambient: float) -> None:
        """
        Advance the temperature by one minute with the doors open.
        The trailer drifts toward the ambient temperature and noise is
        added.

        Parameters
        ----------
        ambient : float
            The ambient temperature in degrees Celsius at the current minute.
        """
        self.temp += self.drift * (ambient - self.temp)
        self.temp += random.gauss(0.0, self.noise_sigma)

    def bump_on_open(self) -> None:
        """
        Apply an instantaneous spike when the doors are opened.  This
        spike models the sudden influx of warm air during a delivery.
        """
        self.temp += self.open_spike