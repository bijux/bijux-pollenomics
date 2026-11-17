# SWEREF 99 projection controls

These fifteen factual coordinates are transcribed from Lantmäteriet's [Kontrollpunkter för SWEREF 99 TM](https://www.lantmateriet.se/contentassets/a7ddfc3b7821498da8b55cd3f71b5150/kontrollpunkter_sweref99tm.pdf), page 1, dated 2007-11-20. The retrieved 68,110-byte PDF has SHA256 `8f51cc34980dbfdc33773b7bc217335664643ebf4a96b1aabec9812d78d2527a`; the PDF itself is not vendored here.

The source geographic columns are latitude then longitude in SWEREF 99. The projected columns are northing then easting in SWEREF 99 TM, printed to 0.001 metre. The CSV names each axis and records easting before northing to match GeoPackage binary X/Y transport. Geographic degree/minute controls are expressed as exact decimal degrees.

Forward tests allow half the printed millimetre plus a 0.000001-metre numerical margin on each projected axis. Inverse tests allow 0.00000002 degree longitude and 0.00000001 degree latitude, sufficient for the printed metre rounding across these 55–69 degree controls. These are projection checks in the same SWEREF 99 frame, not contemporary WGS84/epoch or native-location accuracy tests. Rounded projected controls are not grid-edge fixtures.
