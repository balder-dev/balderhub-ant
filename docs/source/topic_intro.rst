Introduction into Ant
**********************

.. todo provide an explanation of your specific topic that can help others to use your BalderHub project

.. note::
    This package is for development only. This is not a substitute for the official specification and it isn't intended
    to use this package as reference. Have a look at the thisisant.com documentation for more details.

ANT is a proven ultra-low-power (ULP) wireless communications protocol designed for practical wireless sensor networking
in personal area networks (PANs). Developed by Dynastream Innovations (now part of Garmin Canada) and managed by
ANT Wireless, it operates in the 2.4 GHz ISM band and focuses on extremely low power consumption, allowing sensors to
run for years on a single coin-cell battery.

ANT provides a flexible, scalable foundation for low-data-rate applications. It supports multiple simultaneous channels
per device, various network topologies (peer-to-peer, star, and practical mesh), and efficient transfer types
(broadcast, acknowledged, and burst). The protocol abstracts wireless complexity into a compact engine (often paired
with a simple host microcontroller), making it ideal for resource-constrained embedded systems in sports, fitness,
wellness, health monitoring, and IoT/sensor applications. Millions of ANT nodes are deployed worldwide.

ANT+ builds directly on the ANT protocol as a managed network that ensures true interoperability across manufacturers.
While ANT defines the low-level rules for forming networks and transmitting data, ANT+ adds standardized device
profiles for specific use cases (e.g., Heart Rate Monitor, Bike Speed & Cadence, Power Meter, Fitness Equipment).

Each profile specifies exact channel parameters, data formats, and communication behaviors. ANT+ devices use a
shared ANT+ network key and implement one or more profiles, so compatible products from different brands “just work”
together. As the official site states: “ANT+ stands for interoperability”: You can mix sensors and displays (e.g.,
any ANT+ heart-rate strap works with any ANT+ watch, bike computer, or phone app) and expand your system freely.

Key benefits include:

* Ultra-low power and long battery life
* Reliable performance in crowded 2.4 GHz environments
* High node density and multi-channel support
* Seamless multi-brand ecosystems

Note for developers: Public documentation (ANT Message Protocol & Usage, device profiles, etc.) remains freely
available at thisisant.com. The formal ANT+ Adopter Program and certification ended in June 2025, but the open
protocol specifications and reference materials continue to support new implementations.
