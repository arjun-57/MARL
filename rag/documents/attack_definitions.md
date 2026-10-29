# Cyber-Physical Attack Taxonomies & Detection Protocols

## 1. False Data Injection (FDI) Attacks
- **Mechanism**: Adversary intercepts telemetry or forecast packets on the communication bus and adds a malicious bias (e.g. +2.0 MW to solar generation, or cuts reported demand by 50%).
- **Impact**: Misleads coordinator into expecting surplus solar power, leading to inappropriate battery discharge and subsequent feeder undervoltage.
- **Countermeasure**: Check 1 (Physical bounds check: 1.5 MW limit), Check 2 (Temporal gradient check), and Check 4 (Rolling Z-score detector).

## 2. Communication Latency / Delay Attacks
- **Mechanism**: Adversary injects queueing delays (1-3 hours) on critical control packets.
- **Impact**: Coordinator acts on stale prices or outdated feeder load figures.
- **Countermeasure**: Sequence numbering, packet timestamps, and confidence decay.

## 3. Packet Loss Attacks
- **Mechanism**: Drops 30-50% of messages across the bus.
- **Impact**: Coordinator lacks feedback from subordinate agents and falls back to safe default autonomous profiles.

## 4. Agent Failure / Silent Dropout
- **Mechanism**: BESS agent or Demand agent hardware freezes or communication interface crashes.
- **Impact**: Subordinate DER becomes unresponsive.
- **Countermeasure**: Watchdog heartbeat and autonomous local droop/protective control.
