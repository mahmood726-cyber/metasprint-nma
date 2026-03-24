# Release Checklist

## Status
- [x] README present
- [x] LICENSE present
- [x] Developer validation dependencies documented (`requirements.txt`)
- [x] Test suite present
- [x] Public remote configured
- [x] F1000 manuscript artifact present
- [ ] Working tree checked for release cleanliness
- [ ] DOI minted from tagged release

## Before Publishing
1. Run the selenium-based validation scripts listed in `README.md`.
2. Confirm the WebR parity path still passes on the release snapshot.
3. Tag the release and publish the GitHub release.
4. Mint the Zenodo DOI and add it to `CITATION.cff` if desired.
