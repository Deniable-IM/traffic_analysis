# Traffic Analysis Repository for DenIM attacks
This repository is part of a master's thesis focusing on attacking the [DenIM protocol](https://doi.org/10.1109/EuroSP60621.2024.00044) proposed by Nelson et. al. This repository handles the traffic analysis, covering multiple different attacks focusing on identifying deniable messaging. The master's thesis can be found in [Aalborg University's project library](https://kbdk-aub.primo.exlibrisgroup.com/discovery/search?tab=ProjekterSpecialer&search_scope=Projekter&r&sortby=date_d&vid=45KBDK_AUB:DDPB&lang=da&mode=advanced&offset=0&query=lds18,exact,Software,%20Kandidat,AND) under the name *Yet Another Privacy Protocol End-user Reveal*.

## Exponential distribution attack
This attack works by identifying deniable behaviour in $O(n)$ time by assuming all inter-message delays follow an exponential distribution. The limits of this approach is discussed in the thesis.



## Setup
To run this repository you must first set up a virtual environment
```bash
mkdir .venv
python3 -m venv .venv
```

Switch to the venv with
```bash
source .venv/bin/activate
```

To install the dependencies run
```bash
python -m pip install -r requirements.txt
```

If you add packages, remember to update the requirements.txt file with
```bash
python -m pip freeze > requirements.txt
```

PyShark is dependent on TShark which must be installed separately. For Debian-based distros, it can be found in apt.

After the setup, all attacks can be run by using the various classes found in the repository. Examples *might* be provided at some point.



