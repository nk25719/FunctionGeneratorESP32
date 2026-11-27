# Release Candidate Validation Checklist

## Identification

- Candidate version:
- Source commit:
- Package SHA-256:
- Hardware revision:
- Board model:
- Tester:
- Date:

## Automated verification

- [ ] Python regression tests passed.
- [ ] Firmware and web regression tests passed.
- [ ] PlatformIO firmware compiled.
- [ ] Standalone ESP32 firmware compiled.
- [ ] Standalone ESP32-S2 firmware compiled.
- [ ] ADC examples compiled.
- [ ] Package checksums verified.

## Hardware verification

- [ ] Firmware installation successful.
- [ ] Device boots without unexpected errors.
- [ ] Signal outputs are disabled at startup.
- [ ] Channel enable and disable behavior verified.
- [ ] Supported waveforms verified.
- [ ] Frequency accuracy measured.
- [ ] Amplitude accuracy measured.
- [ ] Independent channel operation verified.
- [ ] Settings persistence verified.
- [ ] Wi-Fi connection and reconnection verified.
- [ ] Web interface controls verified.
- [ ] ADC and PWM capture verified where supported.
- [ ] Fault scenarios verified where supported.
- [ ] Heartbeat behavior verified.
- [ ] Output interface and electrical limits verified.

## Measurement evidence

Record measurement equipment, test conditions,
expected results, measured results and deviations.

Unsupported features must be marked N/A with justification.

## Approval

- [ ] No unresolved release-blocking defects.
- [ ] Documentation reviewed.
- [ ] License and distribution permissions confirmed.
- [ ] Maintainer approval obtained.

Decision: PENDING / APPROVED / REJECTED

Approved by:
Date:
