Mahmood Ahmad
Tahir Heart Institute
mahmood.ahmad2@nhs.net

MetaSprint NMA: Zero-Install Browser Network Meta-Analysis with In-Browser R Cross-Validation

Can a zero-install browser application provide clinician-accessible network meta-analysis with built-in R cross-validation for every single computed result? MetaSprint NMA is a single HTML file of 31,500 lines implementing frequentist and Bayesian network meta-analysis with 70 pre-loaded clinical topics spanning 10 therapeutic areas including oncology, cardiology, and nephrology. The application implements the graph-theoretic approach with DerSimonian-Laird, REML, and Paule-Mandel heterogeneity estimation, Bayesian MCMC via Metropolis-Hastings, P-score ranking, node-splitting inconsistency detection, net heat plots, and CINeMA GRADE assessment. Feature comparison showed 23 of 23 assessed capabilities versus 11 of 23 for netmeta and MetaInsight, and all 70 topics produced concordance-verified results against published trial estimates with WebR in-browser validation. Gold-standard regression testing against three canonical datasets confirmed tau-squared, treatment effects, and ranking agreement within all documented tolerances. The platform makes publication-quality NMA accessible to clinicians who lack programming skills. However, a limitation is that WebR validation requires an initial internet connection to load the 20-megabyte R runtime.

Outside Notes

Type: methods
Primary estimand: Treatment effect concordance
App: MetaSprint NMA v1.0
Data: 70 clinical topics across 10 therapeutic areas
Code: https://github.com/mahmood726-cyber/metasprint-nma
Version: 1.0
Validation: DRAFT

References

1. Roever C. Bayesian random-effects meta-analysis using the bayesmeta R package. J Stat Softw. 2020;93(6):1-51.
2. Higgins JPT, Thompson SG, Spiegelhalter DJ. A re-evaluation of random-effects meta-analysis. J R Stat Soc Ser A. 2009;172(1):137-159.
3. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. 2nd ed. Wiley; 2021.
