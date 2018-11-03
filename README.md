ovvo
====

![scatterplot](assets/latin.png?raw=true)

This repository contains the data and accompanying tools for one of my linguistics projects. I set out to examine the (hypothesised) change in Latin word order for transitive verbs from OV to VO. With the kind assistance of the [Corpus Corporum](http://www.mlat.uzh.ch/MLS/index.php?lang=0) I analysed three of their corpora, which are included under a CC-Sharealike (non-commercial) license. These corpora total around 102 million words. The tools and data here should allow all of the findings to be replicated. For the impatient, the raw output data is included in `pass4.csv`.

Requirements
============

To perform the analysis phase (pass3.py) you will need [Collatinus](https://outils.biblissima.fr/en/collatinus) installed, and with the TCP Server active (Menu bar > Extras > Server). I used Collatinus 11.1 on OSX.

The virtual environment was created with Python 3.6.

Process
=======

This should be the whole process:

```bash
source ovvo/bin/activate
unzip cps2.zip -d cps2
unzip cps22.zip -d cps22
unzip cps5.zip -d cps5
./pass0.py
./pass1.py
./pass2.py
./pass3.py
./pass4.py
```

It is very likely that Collatinus 11.1 will crash at some point during `pass3.py` (it seems to have a small memory leak, and I am hitting the TCP Server very hard). You can just restart `pass3.py` and it will pick up where it left off.

For debugging, there are some tools in the `util` directory, provided with no warranty or support.

## Contributing

If you re-analyze the data and discover anything interesting, drop me a line.

For issues with the code, fork and send a pull request or report issues.

## License & Acknowledgements

My code is provided under a BSD style license. See LICENSE file for details.

Corpus Corporum texts (`cps*.zip`) are provided under [CC-BY](https://creativecommons.org/licenses/by-sa/2.5/au/legalcode)

Thanks to the [Collatinus](https://outils.biblissima.fr/en/collatinus) team for assistance and bugfixes

Thanks to [Corpus Corporum](http://www.mlat.uzh.ch/MLS/index.php?lang=0) for allowing access to the texts and assistance with obtaining them in bulk.
