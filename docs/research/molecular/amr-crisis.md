# AMR Crisis, Market Failure, and Ehrlich's Potential

## The Crisis (Hard Numbers)

### Deaths
- **39 million deaths** directly from AMR between 2025-2050 (Lancet, 2024)
- **1.91 million deaths/year** by 2050, up from 1.14 million in 2021
- **8.22 million AMR-associated deaths/year** by 2050 (75% increase from 2021)
- Three deaths every minute from bacterial AMR
- South Asia alone: **11.8 million deaths** by 2050
- Largest increase among 70+ year olds (65.9% of all AMR deaths by 2050)

### Economic Impact
- **$1 trillion** additional healthcare costs by 2050
- **$1-3.4 trillion GDP losses/year** by 2030
- **$176 billion/year** increase in healthcare costs by 2050
- Global output 0.83% lower than business-as-usual

### What Could Help
- Investments in healthcare could **save 92 million lives** by 2050
- Regular new antimicrobials targeting Gram-negative pathogens could **avert 11 million AMR deaths**

Sources:
- https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(24)01867-1/fulltext
- https://wellcome.org/insights/articles/new-forecasts-reveal-39-million-deaths-will-be-directly-attributable-bacterial-antimicrobial
- https://www.worldbank.org/en/topic/health/brief/antimicrobial-resistance-amr

## The Broken System

### Pharma Exodus
- **18 pharma companies** developed antibiotics in the 1980s → **3 today**
- AstraZeneca, Novartis, Sanofi all stopped antibiotic development
- Antibiotics are used for days (not chronic), making ROI terrible vs cancer/diabetes drugs

### Bankruptcy Trail
- **Achaogen (2019):** Spent $300M developing plazomicin. FDA approved it. Revenue after 6 months: <$1M. Filed bankruptcy, assets sold for $16M. Its failure poisoned investor sentiment for the entire sector.
- **Melinta (2019):** $41M in sales, $1B in debt. Second antibiotic developer to go bankrupt that year.
- **90% of antibiotic R&D** is done by small biotechs with market caps <$100M, most pre-revenue

### Pipeline Reality
- **90 antibiotics** in clinical pipeline (down from 97 in 2023)
- Only **12 are innovative**
- Only **4 target WHO "critical" pathogens**
- Only **5 effective against at least one critical priority pathogen**
- Pipeline described as "fragile and failing" by WHO

Sources:
- https://www.nature.com/articles/s41599-024-03452-0
- https://www.cidrap.umn.edu/antimicrobial-stewardship/antibiotic-developer-melinta-files-bankruptcy
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11876093/

## WHO Priority Pathogens (2024)

24 pathogens across 15 families. Critical priority:
- Gram-negative bacteria resistant to last-resort antibiotics
- Drug-resistant Mycobacterium tuberculosis
- Carbapenem-resistant Acinetobacter baumannii (CRAB)
- Carbapenem-resistant Enterobacteriaceae
- MRSA (Staphylococcus aureus)

Major gap: agents targeting metallo-beta-lactamases (increasingly prevalent, almost nothing in pipeline).

Source: https://www.who.int/publications/i/item/9789240093461

## Global Initiatives

### CARB-X
- Funded by BARDA, Wellcome, Germany BMBF, UK GAMRIF, Gates Foundation, Novo Nordisk Foundation
- 2025 round: targeting Gram-negative therapeutics, neonatal sepsis diagnostics, respiratory infection diagnostics
- Source: https://carb-x.org/carb-x-news/carb-x-launches-2025-funding-round-targeting-global-infectious-disease-threats/

### GARDP
- Created by WHO + DNDi in 2016
- Develops treatments for drug-resistant infections
- REVIVE program for antimicrobial research
- Source: https://gardp.org/

### Gr-ADI (New, Feb 2025)
- Gram-Negative Antibiotic Discovery Innovator
- Novo Nordisk Foundation + Wellcome + Gates Foundation
- Seeks: genome-scale tools, resistance propensity selection, bacterial cell penetration understanding

## The Access Gap

### Who's Excluded
- Africa, South America, Southeast Asia **absent from drug discovery datasets**
- LMICs lack computational resources, data science expertise, interdisciplinary teams
- Regulatory agencies in LMICs can't evaluate AI-based approaches
- Proprietary AI methods and datasets increasingly siloed

### The Disparity
- AI drug discovery benefits concentrated in wealthy nations
- Developing world struggles with access to treatments the AI discovers
- Trend toward proprietary methods exacerbates gap
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC11719738/

## Proof That Open Science Works

### COVID Moonshot
- 200 volunteer scientists from 25 countries
- 18,000 compound designs → 2,400 synthesized
- Fragment screen to development candidate in 18 months
- Patent-free, $11M grant for clinical advancement
- Source: https://postera.ai/moonshot/

### Open Source Malaria
- 400 compounds distributed free to 30 countries
- Community-driven, fully open
- Introduced "open source drug discovery" in 2011
- Source: https://journals.plos.org/plospathogens/article?id=10.1371/journal.ppat.1005763

### ZairaChem (Ersilia)
- First fully-automated AI/ML screening cascade in Africa
- Low computational requirements
- Works across broad spectrum of datasets
- Source: https://www.nature.com/articles/s41467-023-41512-2

## Ehrlich's Full Potential

### Immediate (Hackathon)
Prove that an autonomous AI scientist can do real antimicrobial research — literature review, hypothesis design, ML experiments, mechanistic reasoning, candidate ranking — in minutes, for $0.13.

### Short-term (Post-hackathon)
- Open source release attracts academic contributors
- Researchers in LMICs use it for neglected pathogen screening
- Validates against known drug discoveries (Halicin, Abaucin) to build credibility

### Medium-term
- Expand beyond antimicrobials: antifungals (Candida auris), antivirals, neglected tropical diseases
- Integration with automated synthesis labs (Emerald Cloud Lab, Strateos) for wet-lab validation
- Partnership with CARB-X, GARDP, or Ersilia for deployment in Global South

### Long-term Vision
- Template for autonomous scientific investigation on ANY molecular problem
- Democratize drug discovery the way GitHub democratized software
- Every university, every biotech, every country has access to computational drug discovery
- Shift the economics: if the first stage costs $0 instead of $300M, the pipeline can't go bankrupt

### Beyond Antimicrobials

| Problem | Data Source | Impact |
|---------|------------|--------|
| Antifungals | ChEMBL fungal targets | Candida auris is the next MRSA |
| Antivirals | ChEMBL + PDB viral proteins | Pandemic preparedness |
| Neglected tropical diseases | Open Source Malaria patterns | 1B+ people affected, zero pharma interest |
| Anticancer | NCI-60, GDSC datasets | Personalized cancer screening |
| Environmental toxicology | Tox21, ToxCast | Chemical safety assessment |
