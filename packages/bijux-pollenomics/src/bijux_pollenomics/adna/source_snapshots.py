from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ADNA_SOURCE_CAPTURE_BASES",
    "AdnaArchiveSourceSnapshot",
    "build_species_source_snapshots",
    "resolve_archive_source_snapshot",
]

ADNA_SOURCE_CAPTURE_BASES = (
    'ena-study-search',
    'ena-secondary-study-search',
    'ncbi-bioproject-summary',
    'ncbi-nuccore-summary',
    'primary_paper_sample_accession_fallback',
    'curated_scope_note_fallback',
    'paper_title_fallback',
    'curated_note_fallback',
)

_SOURCE_CAPTURED_ON = "2026-05-07"

@dataclass(frozen=True)
class AdnaArchiveSourceSnapshot:
    """Offline source snapshot preserving archive-facing wording for one accession."""

    project_accession: str
    source_family: str
    result_kind: str
    metadata_url: str
    source_title: str
    source_description: str
    title_basis: str
    description_basis: str
    captured_on: str = _SOURCE_CAPTURED_ON

    def as_dict(self) -> dict[str, object]:
        return {
            'project_accession': self.project_accession,
            'source_family': self.source_family,
            'result_kind': self.result_kind,
            'metadata_url': self.metadata_url,
            'source_title': self.source_title,
            'source_description': self.source_description,
            'title_basis': self.title_basis,
            'description_basis': self.description_basis,
            'captured_on': self.captured_on,
        }

_ARCHIVE_SOURCE_SNAPSHOTS = {
  "KU605068-KU605080": {
    "description_basis": "ncbi-nuccore-summary",
    "source_description": "KU605068",
    "source_title": "Camelus dromedarius isolate Palm152 mitochondrion, partial genome",
    "title_basis": "ncbi-nuccore-summary"
  },
  "KX379528-KX379529": {
    "description_basis": "ncbi-nuccore-summary",
    "source_description": "KX379528",
    "source_title": "Canis lupus familiaris isolate CTCdog mitochondrion, complete genome",
    "title_basis": "ncbi-nuccore-summary"
  },
  "PRJEB10854": {
    "description_basis": "ena-study-search",
    "source_description": "Yakutia, Sakha Republic, in the Siberian Far East, represents one of the coldest places on Earth, with winter record temperatures dropping below -70\u00b0C. Nevertheless, Yakutian horses survive all year round in the open air due to striking phenotypic adaptations, including compact body conformations, extremely hairy winter coats and acute seasonal differences in metabolic activities. The evolutionary origins of Yakutian horses and the genetic basis of their adaptations remain, however, contentious. Here we present the complete genomes of nine present-day Yakutian horses and two ancient specimens dating to the early 19th century AD and ~5,200 years ago. By comparing these to the genomes of two Late Pleistocene, 27 domesticated and three wild Przewalski\u2019s horses, we find that contemporary Yakutian horses do not descend from the native horses that populated the region until the mid-Holocene, but were most likely introduced following the migration of the Yakut people a few centuries ago. They, thus, represent one of the fastest cases of adaptation to the extreme temperatures of the Arctic. We find cis-regulatory mutations to have contributed more than non-synonymous changes to their adaptation, likely due to the comparatively limited standing variation within gene bodies at the time the population was founded. Genes involved in hair development, body size, metabolic and hormone signaling pathways represent an essential part of the Yakutian horse adaptive genetic toolkit. Finally, we find evidence for convergent evolution with native human populations and woolly mammoths, suggesting that only a few evolutionary strategies are compatible with survival in extremely cold environments.",
    "source_title": "Tracking the origins of Yakutian horses and the genetic basis for their fast adaptation to arctic environments",
    "title_basis": "ena-study-search"
  },
  "PRJEB19970": {
    "description_basis": "ena-study-search",
    "source_description": "The genomic changes underlying both early and late stages of horse domestication remain largely unknown. We examined the genome sequences of fourteen early domestic horses from the Bronze and Iron Ages, dating to between ~4 and 2.3 thousand years before present (kyr BP). We find selection patterns during early domestication stages supporting the neural crest hypothesis, which provides a unified developmental origin for most common domestic traits. Horses lost genetic diversity and archaic ancestry from a now-extinct lineage. However we observe deleterious mutations arising later than expected under the cost-of-domestication hypothesis, probably following the recent selection of a limited number of reproductive stallions. We also reveal breeding strategies implemented by the Iron Age Scythian steppe nomads, involving selection for robust forelimbs, coat-color variation and no detectable inbreeding.",
    "source_title": "Ancient Genomic Changes Associated with Domestication of the Horse",
    "title_basis": "ena-study-search"
  },
  "PRJEB22390": {
    "description_basis": "ena-study-search",
    "source_description": "The earliest archaeological evidence for horse husbandry derives from the Eneolithic Botai culture of the steppes of Central Asia, ~ 5,500 ya, but the exact nature of early horse domestication remains controversial. We report 42 new ancient genomes of ancient horses (including 20 from Botai) compared with 46 published ancient and modern genomes. We reveal that Przewalski\u2019s horses are the feral descendants of domestic horses first herded at Botai and not the last remaining truly wild horses on the planet. All domestic horses dated from ~4.000 ya to present only show ~2.7% of Botai-related ancestry. This indicates that a massive genomic turnover, coincident with large-scale population migrations of the Early Bronze Age \u201cYamnaya\u201d pastoralists, underpin the expansion of the domestic horse stock that gave rise to modern domesticates.",
    "source_title": "Ancient genomes reveal the ancestry of domestic and Przewalski's horses",
    "title_basis": "ena-study-search"
  },
  "PRJEB30282": {
    "description_basis": "ena-study-search",
    "source_description": "Archaeological evidence indicates that pig domestication had begun by \u223c10,500 y before the present (BP) in the Near East, and mitochondrial DNA (mtDNA) suggests that pigs arrived in Europe alongside farmers \u223c8,500 y BP. A few thousand years after the introduction of Near Eastern pigs into Europe, however, their characteristic mtDNA signature disappeared and was replaced by haplotypes associated with European wild boar. This turnover could be accounted for by substantial gene flow from local European wild boar, although it is also possible that European wild boar were domesticated independently without any genetic contribution from the Near East. To test these hypotheses, we obtained mtDNA sequences from 2,099 modern and ancient pig samples and 63 nuclear ancient genomes from Near Eastern and European pigs. Our analyses revealed that European domestic pigs dating from 7,100 to 6,000 y BP possessed both Near Eastern and European nuclear ancestry, while later pigs possessed no more than 4% Near Eastern ancestry, indicating that gene flow from European wild boar resulted in a near-complete disappearance of Near East ancestry. In addition, we demonstrate that a variant at a locus encoding black coat color likely originated in the Near East and persisted in European pigs. Altogether, our results indicate that while pigswere not independently domesticated in Europe, the vast majority of human-mediated selection over the past 5,000 y focused on the genomic fraction derived from the European wild boar, and not on the fraction that was selected by early Neolithic farmers over the first 2,500 y of the domestication process.",
    "source_title": "Ancient pigs reveal a near-complete genomic turnover following their introduction to Europe",
    "title_basis": "ena-study-search"
  },
  "PRJEB31613": {
    "description_basis": "ena-study-search",
    "source_description": "Horse domestication revolutionized warfare and accelerated travel, trade and the geographic expansion of languages. Here we present the largest DNA time-series for a non-human organism to date, including genome-scale data from 149 ancient animals and 129 ancient genomes (\u22651-fold coverage), 87 of which are new. This extensive dataset allows us to assess the modern legacy of past equestrian civilisations. We find that two extinct horse lineages existed during early domestication, one at the far western (Iberia) and the other at the far eastern range (Siberia) of Eurasia. None of these contributed significantly to modern diversity. We show that the influence of Persian-related horse lineages increased following the Islamic conquests in Europe and Asia. Multiple alleles associated with elite-racing, including at the MSTN \u201cspeed gene\u201d, only rose in popularity within the last millennium. Finally, the development of modern breeding impacted genetic diversity more dramatically than the previous millennia of human management.",
    "source_title": "Tracking five millennia of horse management with extensive ancient genome time-series",
    "title_basis": "ena-study-search"
  },
  "PRJEB31621": {
    "description_basis": "ena-study-search",
    "source_description": "Using ancient DNA, we investigate the history of cattle domestication in the Near East. NOTE: some fastq files have been generated from the same PCR. These are noted as such in the Library Name metadata for each fastq. Please using the library metadata for RGLB when assigning read groups, and for each sample remove duplicates following merging of aligned fastq files. NOTE: for some samples, only trimmed fastq files (\"sample_trimmed.fastq.gz\") have been uploaded. These were generated with the following cutadapt (https://cutadapt.readthedocs.io/en/stable/guide.html) command: cutadapt -a AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC -O 1 -m 30 NOTE: all data has been treated with Uracil DNA endonuclease EXCEPT where noted in the Library metadata. Specifically, this refers to Bub1 and certain fastq files for Th7.",
    "source_title": "Ancient cattle genomics of the Near East.",
    "title_basis": "ena-study-search"
  },
  "PRJEB36540": {
    "description_basis": "ena-study-search",
    "source_description": "Sheep was among the first domesticated animals, but its demographic history is little understood. Here we present a combined analyses of mitochondrial DNA and genome-wide polymorphism data from ancient central and west Anatolian sheep dating to the early Holocene. First, we observe strong loss of mitochondrial haplotype diversity around 7500 BCE during the early Neolithic, consistent with a domestication-related bottleneck. Post-7000 BCE, mitochondrial haplogroup diversity increases, compatible with admixture from other domestication centers and/or from wild populations. Analysing archaeogenomic data, we further find that Anatolian Neolithic sheep (ANS) are genetically closest to present-day European breeds, and especially those from central and north Europe. Our analysis revealed that Asian contribution to south European breeds, possibly during the Bronze Age, could partly explain this pattern.",
    "source_title": "Archaeogenetic analysis of Neolithic sheep from Anatolia suggests a complex demographic history since domestication",
    "title_basis": "ena-study-search"
  },
  "PRJEB41594": {
    "description_basis": "ena-study-search",
    "source_description": "The development and dispersal of agropastoralism transformed the cultural and ecological landscapes of the Old World, but little is known about when or how this process first impacted Central Asia. Here, we present archaeological/biomolecular evidence from Obishir V in southern Kyrgyzstan, establishing the presence of domesticated sheep by ca. 6,000 BCE. Zooarchaeological and collagen peptide mass fingerprinting show exploitation of Ovis and Capra, while cementum analysis of intact teeth implicates possible pastoral slaughter during the fall season. Most significantly, ancient DNA reveals these directly dated specimens as the domestic O. aries, within the genetic diversity of domesticated sheep lineages. Together, these results provide the earliest evidence for the use of livestock in the mountains of the Ferghana Valley, predating previous evidence by 3,000 years and suggesting that domestic animal economies reached the mountains of interior Central Asia far earlier than previously recognized.",
    "source_title": "Evidence for early dispersal of domestic sheep into Central Asia",
    "title_basis": "ena-study-search"
  },
  "PRJEB43564": {
    "description_basis": "ena-study-search",
    "source_description": "Horses and donkeys have had a far-reaching impact on human history, providing mechanical power for agriculture and transportation. Their F1-hybrids, especially mules, have also been of considerable importance due to their exceptional strength, endurance and resistance. The reconstruction of the respective role that horses, donkeys and mules played in past societies requires prior identification of their osseous elements in archaeological assemblages. This, however, remains difficult on the basis of morphological data alone and in the absence of complete skeletal elements. While DNA sequencing provides almost certain identification success, this approach requires dedicated infrastructure and sufficient ancient DNA (aDNA) preservation. Here, we assessed the performance of a cost-effective alternative approach based on geometric morphometric (GMM) analysis of the bony labyrinth, a structure carried within the petrosal bone. This extremely compact osseous structure provides good aDNA preservation and is frequently found in archaeological assemblages. To assess the GMM performance, we first used High-throughput DNA sequencing to identify 41 horses, 24 donkeys, 36 mules and one hinny from 11 archaeological sites from France and Turkey spanning different time periods. This provided a panel of 102 ancient equine remains for micro-computed tomography (microCT) and GMM assessment of the variation of the bony labyrinth shape, including the cochlea and the semicircular canals. Our new method shows good-to-excellent prediction rates (85.7%-95.2%) for the identification of species and hybrids when considering the cochlea and semicircular canals together. It provides a cheap, non-destructive alternative to aDNA for the taxonomic identification of past equine assemblages.",
    "source_title": "Assessing the predictive taxonomic power of the bony labyrinth 3D shape in horses, donkeys and their F1-hybrids",
    "title_basis": "ena-study-search"
  },
  "PRJEB44430": {
    "description_basis": "ena-study-search",
    "source_description": "Horse domestication fundamentally transformed long-range mobility and warfare. However, modern domesticates do not descend from the earliest domestic horse lineage associated with archaeological evidence of bridling, milking and corralling at Botai, Central Asia ~3,500 BCE (Before Common Era). Other long-standing candidate regions for horse domestication, such as Iberia and Anatolia, were also recently challenged. Therefore, the genetic, geographic and temporal origins of modern domestic horses remained unknown. Here, we pinpoint the Western Eurasian steppes, especially the lower Volga-Don region, as the homeland of modern domestic horses. Furthermore, we map the population changes accompanying domestication from 273 ancient horse genomes. This reveals that modern domestic horses ultimately replaced almost all other local populations as they rapidly expanded across Eurasia from ~2,000 BCE, synchronously with equestrian material culture, including Sintashta spoke-wheeled chariots. We find that equestrianism involved strong selection for critical locomotor and behavioral adaptations at the GSDMC and ZFPM1 genes. Our results reject the commonly held association between horseback riding and the massive expansion of Yamnaya steppe pastoralists into Europe ~3,000 BCE driving the spread of Indo-European languages. This contrasts with the situation in Asia where Indo-Iranian languages, chariots and horses spread together, following the early second millennium BCE Sintashta culture.",
    "source_title": "The origins and spread of domestic horses from the Western Eurasian steppes",
    "title_basis": "ena-study-search"
  },
  "PRJEB50952": {
    "description_basis": "ena-study-search",
    "source_description": "Ancient DNA preservation in subfossil specimens provides a unique opportunity to retrieve genetic information from the past. As ancient DNA extracts are generally dominated by molecules originating from environmental microbes, capture techniques are often used to economically retrieve orthologous sequence data at the population scale. Post-mortem DNA damage, especially the deamination of cytosine residues into uracils, also considerably inflates sequence error rates unless ancient DNA extracts are treated with the USER enzymatic mix prior to library construction. While both approaches have recently gained popularity in ancient DNA research, the impact of USER-treatment on capture efficacy still remains untested. In this study, we applied hyRAD capture to eight ancient equine subfossil specimens from France (1st-17th century CE), including horses, donkeys and their first-generation mule hybrids. We found that USER-treatment could reduce capture efficacy and introduce significant experimental bias. It differentially affected the size distribution of on-target templates following capture with two distinct hyRAD probe sets in a manner that was not driven by differences in probe sizes and DNA methylation levels. Finally, we recovered unbalanced proportions of donkey-specific and horse-specific alleles in mule capture sequence data, due to the combined effects of USER-treatment, probe sets and reference bias. Our work demonstrates that while USER-treatment can improve the quality of ancient DNA sequence data, it can also significantly affect hyRAD capture outcomes, introducing bias in the sequence data that is difficult to predict based on simple molecular probe features. Such technical batch effects may prove easier to model and correct for using capture with synthetic probes of controlled sizes and diversity content.",
    "source_title": "Assessing the impact of USER-treatment on hyRAD capture applied to ancient DNA",
    "title_basis": "ena-study-search"
  },
  "PRJEB52590": {
    "description_basis": "ena-study-search",
    "source_description": "Mules, which have been valued in the Mediterranean basin since the Iron Age, became integrated into the animal world north of the Alps in the course of Romanization. Until now, however, their true contribution to the economic and military life in the northern Roman provinces Raetia, Noricum and Upper Pannonia (southern Germany, eastern Switzerland and Austria) has remained unknown in the absence of robust identification methods based on morphometric approaches. We confronted morphological identification of 405 equid specimens collected in the Late Iron Age (Celtic) (~2nd \u2013 1st century (c.) BCE) and Roman (~1st \u2013 5th c. CE) archaeological contexts with their ancient DNA signatures. Our multi-method study demonstrates that, although ancient DNA and morphological approaches (including standard osteomorphology and geometric morphometrics) provide overall >85% matching results, in the case of hybrid animals, the extent of overlap with ancient DNA drops to \u226452%. Out of five skeletal elements studied here (mandibular premolars and molars, metapodials, humeri and tibiae), only premolar mandibular teeth (P3, P4) provide good enough accuracy in hybrid classification (89%) based on geometric morphometrics, making it the preferred element and method in future zooarchaeological studies, when ancient DNA data is not available. Our data show that, although not yet present in the preceding Iron Age, one in six equids in Roman times is a mule, suggesting a strong Mediterranean influence on the use of equids in daily life north of the Alps.",
    "source_title": "Ancient DNA refines Taxonomic Classification of Roman Equids North of the Alps, elaborated with Osteomorphology and Geometric Morphometrics",
    "title_basis": "ena-study-search"
  },
  "PRJEB52849": {
    "description_basis": "ena-study-search",
    "source_description": "Donkeys transformed human history as beasts of burden for long-distance movement, connecting societies, especially across semi-arid and upland environments. They are globally expanding and provide key support to low-to-middle income communities. Donkeys remain, however, largely understudied at the genomic level, due to their generally depreciated status. To elucidate their origins, spread, and historical management practices, we constructed a comprehensive genome panel of 207 modern and 31 ancient donkeys, including 15 wild equids. The strong phylogeographic structure among modern subpopulations suggests that donkeys were domesticated once in Africa ~5,000BCE, before rapidly spreading and differentiating into Europe and Asia ~2,500BCE. We also uncover back migration into modern Nubia and Maghreb, secondary contacts with Europe impacting western Africa, a previously unknown divergent lineage in the Levant and a Roman mule breeding center. Donkey management involved wilf introgression and inbreeding for mule production. Our work reveals dramatically different domestication histories in horses and donkeys.",
    "source_title": "Ancient and modern genomes elucidate the origins, spread and management practices underlying donkey domestication.",
    "title_basis": "ena-study-search"
  },
  "PRJEB55549": {
    "description_basis": "ena-study-search",
    "source_description": "Ancient and modern genomes elucidate the origins, spread and management practices underlying donkey domestication.",
    "source_title": "The genomic history and global expansion of domestic donkeys",
    "title_basis": "ena-study-search"
  },
  "PRJEB56293": {
    "description_basis": "ena-study-search",
    "source_description": "The age profiles of archaeological bone assemblages inform on past animal management practices, with overkilling of male juveniles indicating resource optimization for livestock production. Age profiling of ancient animals is, however, not always possible due to the fragmentary nature of the fossil record and the lack of age skeletal markers valid across species. DNA methylation patterns at CpG clock sites represent an almost universal biological clock for mammals and can be deduced in ancient osteological remains from signatures of post-mortem DNA damage. Estimating the age-at-death of ancient individuals from DNA methylation patterns remains, however, challenging, as both subject to technical artefacts and requiring extensive sequence coverage. Here, we take advantage of the recently developed DNA methylation clock based on 31,836 CpG sites and the availability of dental age markers in horses to assess age predictions in 85 ancient remains. We establish the reliability of our approach using whole genome sequencing and develop an in-solution target-enrichment assay for 2,171 CpG sites, providing accurate estimates for only a fraction of the cost. The 85 assemblages investigated reveal similar age profiles across lineages, sex, ritual and non-ritual activities. We also leverage 59 differentially methylated sites in castrated and non-castrated males aged above 11 years to assess castration practice in the past. We reject previous contention that the Pazyryk horses sacrificed 2,300 years ago at Berel\u2019, Kazakhstan were castrated. Our methodology opens for a deeper characterization of past husbandry and ritual practices and holds the potential to reveal age mortality profiles in ancient societies, once extended to human remains.",
    "source_title": "Epigenetic prediction of age-at-death and castration in ancient horses",
    "title_basis": "ena-study-search"
  },
  "PRJEB57293": {
    "description_basis": "ena-study-search",
    "source_description": "Anthropogenic reintroduction can supplement natural recolonisation in reestablishing a species\u2019 distribution and abundance. However, both reintroductions and recolonisations can give rise to population bottlenecks that reduce genetic diversity and increase inbreeding, potentially causing accumulation of genetic load and reduced fitness. Most current populations of the endemic high-arctic Svalbard reindeer (Rangifer tarandus platyrhynchus) originate from recent reintroductions or recolonisations following regional extirpations due to past overharvesting. We investigated and compared the genomic consequences of these two paths to reestablishment using whole-genome shotgun sequencing of 100 Svalbard reindeer across their range. We found little admixture between reintroduced and natural populations. Two reintroduced populations, each founded by 12 individuals around four decades (i.e. 8 reindeer generations) ago, formed two distinct genetic clusters. Compared to the source population, these populations showed only small decreases in genome-wide heterozygosity and increases in inbreeding and lengths of runs of homozygosity. In contrast, the two naturally recolonised populations without admixture possessed much lower heterozygosity, higher inbreeding, and longer runs of homozygosity, possibly caused by serial population bottlenecks and/or fewer or more genetically related founders than in the reintroduction events. Naturally recolonised populations can thus be more vulnerable to the accumulation of genetic load than reintroduced populations. This suggests that in some organisms even small-scale reintroduction programs based on genetically diverse source populations can be more effective than natural recolonisation in establishing genetically diverse populations. These findings warrant particular attention in the conservation and management of populations and species threatened by habitat fragmentation and loss.",
    "source_title": "Population genomics of Svalbard reindeer",
    "title_basis": "ena-study-search"
  },
  "PRJEB59481": {
    "description_basis": "ena-study-search",
    "source_description": "Sheep were domesticated 10-12 thousand years ago (kya) in western Asia. Sheep spread across Europe with the Neolithic expansion and had reached Scandinavia by around 5 kya. At the same time the first wool economies started to become established in the Near East, probably associated with a new type of sheep breeds which later expanded across Europe. Northern European short-tailed sheep are believed to be remnants of the first expansion of meat sheep. Very little is known about the genomics of early sheep in northern Europe with most studies to date focusing on uniparental markers or retrovirus genotypes. In this study we investigate the genomic history of sheep in the Baltic-sea area with a focus on Sweden and Finland. We present five new high quality ancient sheep genomes from two islands, Gotland and \u00c5land, dating from the Late Neoltihic to the late Medieval/early Vasa. We compare these genomes to a large panel of modern breeds from across the world with a focus on northern European breeds. We investigate what happened genetically in Scandinavian sheep from their introduction up until modern times.",
    "source_title": "Ancient sheep genomes from Baltic islands",
    "title_basis": "ena-study-search"
  },
  "PRJEB60484": {
    "description_basis": "ena-study-search",
    "source_description": "Overharvest can lead to near-extirpation of a species and can therefore drastically impact its genetic diversity and gene pool, threatening its future adaptability. Overharvest has extensively happened in the past, but remains a contemporary issue especially for Arctic mammals, which now confront the fastest changing environment on Earth due to climate change. The high-Arctic Svalbard reindeer (Rangifer tarandus platyrhynchus), endemic to the Svalbard archipelago, experienced a harvest-induced bottleneck that occurred throughout the 17th to 20th centuries. We here investigate changes in genetic diversity, population structure and gene-specific differentiation before, during, and after this overharvesting event. Using shotgun sequencing, we generated the first ancient nuclear and mitochondrial genomes from Svalbard reindeer (n = 18, up to 4000 BP). Together with a large collection of modern genomes (n = 90), we were able to infer temporal changes. Our results indicate that hunting triggered drastic genetic changes and restructuring in reindeer populations. Median heterozygosity was reduced by 23%, while the mitochondrial genetic diversity was reduced only to a limited extent, likely due to a complex post-harvest recolonization process and low diversity already in ancient times. This population structuring post-harvest happened during a period in which the reduced formation of sea-ice was further isolating these reindeer populations, such that altered climatic conditions worsened the consequences of overharvesting. Near-extirpation also altered the allele frequencies of important genes contributing to a variety of basic biological systems (e.g., cardiovascular, pulmonary, immune, reproductive, digestive, and central nervous systems). The genomic erosion and genetic isolation of Svalbard reindeer populations will likely play a major role in how metapopulation dynamics (i.e., extirpation, recolonization) of the species will cope with further climate change, thus for Svalbard reindeer conservation we stress the need to understand the long-term interplay of harvesting recovery and increasing landscape fragmentation.",
    "source_title": "Overhunting of Svalbard reindeer",
    "title_basis": "ena-study-search"
  },
  "PRJEB61721": {
    "description_basis": "ena-study-search",
    "source_description": "Understanding the evolution of declining and endangered populations is of crucial significance in evolutionary and conservation biology. Since island populations are typically much smaller than those from their mainland range, they are ideal systems to examine threats such as loss of genetic diversity and adaptive potential as well as accumulation of deleterious variation. The Svalbard reindeer (Rangifer tarandus platyrhynchus) is an endemic wild subspecies that colonised the Svalbard archipelago ca. 7,000 years ago and that shows numerous physiological and morphological adaptations to its challenging high-arctic habitat. Here, we leverage a de-novo chromosome-level assembly for R. t. platyrhynchus and analyse 132 reindeer genomes spanning most of its Holarctic range, including 91 genomes from Svalbard to examine the genomic consequences of long-term isolation and small population size in this insular subspecies. Empirical data, demographic reconstructions, and forward simulations show that long-term isolation and an associated high level of inbreeding may have facilitated the reduction of highly deleterious\u2014and to a lesser extent, moderately deleterious\u2014variation. Importantly, our study shows that long-term reduced genetic diversity did not preclude local adaptation to the arctic environment. Thus, even a severely bottlenecked and isolated population can retain evolutionary potential.",
    "source_title": "Genomic erosion in Svalbard reindeer",
    "title_basis": "ena-study-search"
  },
  "PRJEB61808": {
    "description_basis": "ena-study-search",
    "source_description": "We report over 100 ancient genomes of sheep, principally from domestic Ovis aries but also from wild Ovis gmelini and Ovis vignei. Please note that the uploaded data is RAW and has not been trimmed for adaptors, due to variation in how groups and pipelines handle data. Please refer to the associated publication for steps on how to replicate our adaptor filtering.",
    "source_title": "Ancient genomes of sheep from Eurasia spanning ten millenia",
    "title_basis": "ena-study-search"
  },
  "PRJEB69690": {
    "description_basis": "ena-study-search",
    "source_description": "Being amongst the first domesticated animal species, the demographic history of sheep is not yet fully understood. Previous findings suggest a complex population history with widespread intercontinental admixture, and point to Southwest Asia as a potential domestication center. Here, we study the domestication history of sheep with pale genomes from Anatolia (n=15), Iran (n=2) and South Russia (n=1). We also incorporate present-day genomes from Anatolian (n=5) and Cypriot mouflon (n=10), which are suggested as close relatives or feralized remnants of domestic sheep. We further study these mouflon populations in a conservation genomics perspective, as they are currently listed as endangered and have comprised small population sizes with multiple bottlenecks in the last decades.",
    "source_title": "Genomic insights into population history of sheep",
    "title_basis": "ena-study-search"
  },
  "PRJEB7537": {
    "description_basis": "ena-study-search",
    "source_description": "The domestication of the horse ~5,500 BP and the emergence of mounted riding, chariotry and cavalry, dramatically transformed human civilization. However, the genetics underlying horse domestication is difficult to reconstruct given the near extinction of wild horses. We therefore sequenced two ancient horse genomes from Taymyr, Russia (at 7.4 and 24.3X coverage), which both predate the earliest archeological evidence of domestication. We compared these with genomes of domesticated horses and the wild Przewalski's horse and found genetic structure within Eurasia in the Late Pleistocene, with the ancient population contributing significantly to the genetic variation of domesticated breeds. We furthermore identified a conservative set of 125 potential domestication targets using four complementary scans for genes that have undergone positive selection. One group of genes is involved in muscular and limb development, articular junctions and the cardiac system, and may represent physiological adaptation towards human utilization. A second group consists of genes with cognitive functions, including social behavior, learning capabilities, fear response and agreeableness, which may have been key for taming horses. We also found that domestication is associated with inbreeding and an excess of deleterious mutations. This is in line with the 'cost of domestication' hypothesis also reported for rice, tomatoes and dogs, and generally attributed to the relaxation of purifying selection resulting from the strong demographic bottlenecks accompanying domestication. Our work demonstrates the power of ancient genomes to reconstruct the complex genetic changes that transformed wild animals into their domesticated forms, and the population context in which these took place.",
    "source_title": "Prehistoric genomes reveal the genetic foundation and cost of horse domestication",
    "title_basis": "ena-study-search"
  },
  "PRJEB75467": {
    "description_basis": "ena-study-search",
    "source_description": "Now extinct, the aurochs (Bos primigenius) was a keystone species in prehistoric Eurasian and North African ecosystems, and the progenitor of cattle (Bos taurus), a domesticate that has provided people with food and labour for millennia. Here we analysed 38 ancient genomes that revealed four distinct ancestries of aurochs: European, Near Eastern, North Asian and South Asian, each of which has dynamic trajectories that have responded to changes in climate and culture. Like Homo heidelbergensis, aurochsen first entered Europe ~650 kya, but these early populations leave only trace ancestry after population replacement from the east ~90 kya during an MIS5 warm period before the onset of the most recent glaciation. Asian and European populations then remained separated by habitat fragmentation until mixing following the climate amelioration of the early Holocene. European aurochsen endured the more severe bottleneck during the Last Glacial Maximum, retreating to southern refugia before recolonising from Iberia. Domestication involved limited capture of a southwest Asian aurochs population, followed by early and pervasive male-mediated admixture with each ancestral strain of aurochs after domestic stocks dispersed beyond their Near Eastern region of origin.",
    "source_title": "The genomic natural history of the aurochs",
    "title_basis": "ena-study-search"
  },
  "PRJEB81145": {
    "description_basis": "ena-study-search",
    "source_description": "Sheep was one of the first domesticated animals in Neolithic West Eurasia. The zooarchaeological record suggests that domestication first took place in Southwest Asia, although much remains unresolved about the precise location(s) and timing(s) of earliest domestication, or the post-domestication history of sheep. Here we present new 24 partial sheep paleogenomes, including one from late Palaeolithic/Late Glacial and 14 from Neolithic Anatolia, two from Neolithic Iran, two from Neolithic Iberia, three from Neolithic France, and one each from mid-Holocene Baltic and South Russia, in addition to five present-day Central Anatolian Mouflons and two present-day Cyprian Mouflons. We find that domestic sheep breeds are genetically closer to the Anatolian Epipaleolithic sheep, as well as the present-day Anatolian and Cyprian Mouflon than the Iranian Mouflon. This supports a Central Anatolian source for domestication, the first clear-cut evidence of a domestication process in SW Asia outside the Fertile Crescent, although we cannot rule out multiple domestication events also within the Neolithic Fertile Crescent. We further find evidence for multiple admixture and replacement events, including one that parallels the Yamnaya expansion in humans and a post-Bronze Age event that appears to have introduced Asia-related alleles across global sheep breeds. Our findings mark the dynamism of past domestic sheep populations in their potential for dispersal and admixture, sometimes being paralleled by their shepherds and in other cases not. These sequences are those from the three Neolithic sheep from France reported in this paper by Kaptan et al, in press in MBE.",
    "source_title": "Neolithic Sheeps from France",
    "title_basis": "ena-study-search"
  },
  "PRJEB81815": {
    "description_basis": "ena-study-search",
    "source_description": "The domestic cat (Felis catus) descend from the African wildcat subspecies Felis lybica lybica. Its global distribution alongside humans testifies to its successful adaptation to the anthropogenic environment. Uncertainty remains regarding whether cats originated in the Levant, Egypt or elsewhere, when that process took place, and how cats dispersed into Europe. By generating 87 ancient and modern cat genomes, we demonstrate that cats did not spread to Europe with Neolithic farmers. Our results suggest a more recent (1st millennium BCE) date for cat domestication and that North Africa was the original source of the modern global domestic gene pool. We show that North African cats were introduced to Europe at least twice from genetically distinct populations.",
    "source_title": "Ancient DNA from wild and domestic cats in Europe",
    "title_basis": "ena-study-search"
  },
  "PRJEB90141": {
    "description_basis": "ena-study-search",
    "source_description": "Identification of Variations in Goat genomes related to domestication and adaptation",
    "source_title": "VarGoats \u2013 Detection of domestic and wild goat variants",
    "title_basis": "ena-study-search"
  },
  "PRJEB90261": {
    "description_basis": "ena-study-search",
    "source_description": "Archaeological and human paleogenomic evidence gathered on the indigenous people of the Canary Islands have showed that their geographical origin was North Africa. Radiocarbon data also indicate that, excluding the temporal occupation of the islet of Lobos by Romans (1st century BCE \u2013 1st century CE), the archipelago was permanently colonized from 2nd \u2013 3rd century CE by Amazigh communities. The Canary Islands were seemingly forgotten in the following centuries by Western societies, until the beginning of the European Age of Exploration in the 14th century. An alternative approach to study the people of the Canary Island is analyzing the domesticates that they introduced in the archipelago. In this study, we present 52 complete mitogenomes of ancient Canarian goats, encompassing samples from the Roman site of Lobos, the indigenous occupation phase and the colonial period of the archipelago. We observe that the mitogenomes present in indigenous goats are classified in two haplogroup A clades associated to Middle Eastern and North African goats, consistent with a North African origin for the indigenous population of the Canaries. The median-joining network has a star shape, with two basal haplogroups present in all islands and a subsequent radiation of isolated haplotypes, suggesting a founder effect in the Canary Islands. The indigenous goats show low matrilineal diversity and mostly non-shared derived lineages between islands, both pointing to a lack of gene flow. Interestingly, the goats from Lobos share the same haplotypes as the indigenous population indicating that the Roman and Amazigh settlements briefly overlapped and the goats in Lobos were most probably taken from the neighboring islands. We also detect temporal continuity in the mitochondrial DNA composition from the indigenous period to the colonial society and present-day goats, suggesting European settlers exploited this well-adapted species and the indigenous management knowledge.",
    "source_title": "Paleogenomic analysis of complete mitochondrial DNA sequences from ancient goats from the Canary Islands",
    "title_basis": "ena-study-search"
  },
  "PRJEB9799": {
    "description_basis": "ena-study-search",
    "source_description": "Completed in 2009, the reference genome assembly of the domesticated horse (EquCab 2.0) produced the majority of publically available annotations of genetic variations in this species. Following that effort, a few other projects that focused at variant discovery of a particular breed or two. In this project we aim to identify and annotate single nucleotide polymorphisms (SNPs), insertions and deletions (INDELs), copy number variations (CNVs) and structural variations (SVs) in the genomes six horses of diverse genetic background using next generation sequencing.",
    "source_title": "Whole genome detection of sequences of six horses from diverse breeds.",
    "title_basis": "ena-study-search"
  },
  "PRJNA1178732": {
    "description_basis": "ncbi-bioproject-summary",
    "source_description": "Raw sequencing data for ancient Chinese leopard cats (Prionailurus bengalensis) and domestic cats (Felis catus)",
    "source_title": "Leopard Cats Occupied Human Settlements in China for 3,500 years before the Arrival of Domestic cats in the 600-900 CE",
    "title_basis": "ncbi-bioproject-summary"
  },
  "PRJNA1328209": {
    "description_basis": "ena-study-search",
    "source_description": "we generated ancient genomic data from five goat individuals dating back approximately 3,600 years before present (BP) in the Lake Qinghai Basin.",
    "source_title": "Approximately 3,600-year-old genomic data from ancient goat populations in the Lake Qinghai Basin.",
    "title_basis": "ena-study-search"
  },
  "PRJNA421430": {
    "description_basis": "ena-study-search",
    "source_description": "DNA extracted from Sus scrofa tissues used to test the effect of varying temperatures and concentrations of NaCl on rates of cytosine deamination in mammalian DNA. Used to develop rate estimates of ancient DNA damage under marine conditions.",
    "source_title": "Sus scrofa Raw sequence reads",
    "title_basis": "ena-study-search"
  },
  "PRJNA634908": {
    "description_basis": "ncbi-bioproject-summary",
    "source_description": "Parallel evolution can occur through novel mutations, standing genetic variation, or adaptive introgression. Uncovering parallelism and introgressed populations can complicate management of threatened species, particularly as admixed populations are not generally considered under conservation legislations. We examined high coverage whole-genome sequences of 30 caribou (Rangifer tarandus) from across North America and Greenland, representing divergent intra-specific lineages, to investigate parallelism and levels of introgression contributing to the formation of ecotypes. Caribou are split into four subspecies and 11 extant conservation units, known as Designatable Units (DUs), in Canada. Using genomes from all four subspecies and six DUs, we undertake demographic reconstruction and confirm two previously inferred instances of parallel evolution in the woodland subspecies and uncover an additional instance of parallelism of the eastern migratory ecotype. Detailed investigations reveal introgression in the woodland subspecies, with introgressed regions found spread throughout the genomes encompassing both neutral and functional sites. Our comprehensive investigations using whole genomes highlight the difficulties in unequivocally demonstrating parallelism through adaptive introgression in non-model species with complex demographic histories, with standing variation and introgression both potentially involved. Additionally, the impact of parallelism and introgression on the designation of conservation units has not been widely considered, and the caribou designations will need amending in light of our results.",
    "source_title": "Introgression and ecotypic parallelism in caribou (Rangifer tarandus)",
    "title_basis": "ncbi-bioproject-summary"
  },
  "PRJNA705960": {
    "description_basis": "ena-study-search",
    "source_description": "Domestic cattle were brought to Spain by early settlers and agricultural societies. Due</p><p>to missing Neolithic sites in the Spanish region of Galicia, very little is known about</p><p>this process in this region. We sampled 18 cattle subfossils from different ages and</p><p>different mountain caves in Galicia, of which 11 were subject to sequencing of the</p><p>mitochondrial genome and phylogenetic analysis, to provide insight into the</p><p>introduction of cattle to this region. We detected high similarity between samples from different time periods and were able to compare the time frame of the first domesticated</p><p>cattle in Galicia to data from the connecting region of Cantabria to show a plausible</p><p>connection between the Neolithization of these two regions. Our data shows a close</p><p>relationship of the early domesticated cattle of Galicia and modern cow breeds and</p><p>gives a general insight into cattle phylogeny. We conclude that settlers migrated to this</p><p>region of Spain from Europe and introduced common European breeds to Galicia.",
    "source_title": "aDNA sequencing of Galician cattle mitochondrial genomes",
    "title_basis": "ena-study-search"
  },
  "PRJNA788987": {
    "description_basis": "ena-study-search",
    "source_description": "Whole genome re-sequencing data of 7 ancient Chinese pigs",
    "source_title": "Sus scrofa Raw sequence reads",
    "title_basis": "ena-study-search"
  },
  "PRJNA878488": {
    "description_basis": "ena-study-search",
    "source_description": "Retracing the ancient human migration routes in the remote islands of the Pacific relies on robust models of the origins and spread of animals that were commensal to long-distance ocean voyag-es. Domestic pigs (Sus scrofa) in Polynesia belong to a rare mitochondrial DNA group whose ge-ographic origins are disputed. We report new complete genome ancient DNA that suggests all founding populations of pigs in Polynesia, first settled by people about 2800-700 years ago, can be traced back to northern peninsular Southeast Asia.",
    "source_title": "Sus scrofa Raw sequence reads",
    "title_basis": "ena-study-search"
  },
  "SRP073444": {
    "description_basis": "ena-secondary-study-search",
    "source_description": "DNA sequences from ancient domestic and wild dromedary camel",
    "source_title": "Camelus dromedarius Raw sequence reads",
    "title_basis": "ena-secondary-study-search"
  },
  "SRS1407451": {
    "description_basis": "curated_scope_note_fallback",
    "source_description": "Ancient dog CTC sample explicitly named on the primary paper page.",
    "source_title": "Ancient European dog genomes reveal continuity since the Early Neolithic",
    "title_basis": "primary_paper_sample_accession_fallback"
  },
  "SRS1407453": {
    "description_basis": "curated_scope_note_fallback",
    "source_description": "Ancient dog HXH sample explicitly named on the primary paper page.",
    "source_title": "Ancient European dog genomes reveal continuity since the Early Neolithic",
    "title_basis": "primary_paper_sample_accession_fallback"
  }
}

def resolve_archive_source_snapshot(project) -> AdnaArchiveSourceSnapshot:
    """Resolve the offline source snapshot for one curated archive record."""
    payload = _ARCHIVE_SOURCE_SNAPSHOTS[project.project_accession]
    return AdnaArchiveSourceSnapshot(
        project_accession=project.project_accession,
        source_family=project.source_family,
        result_kind=project.result_kind,
        metadata_url=project.metadata_url,
        source_title=str(payload["source_title"]),
        source_description=str(payload["source_description"]),
        title_basis=str(payload["title_basis"]),
        description_basis=str(payload["description_basis"]),
    )

def build_species_source_snapshots(species_name: str) -> tuple[AdnaArchiveSourceSnapshot, ...]:
    """Return source snapshots for one tracked species root."""
    from .ena import build_species_archive_projects

    return tuple(
        resolve_archive_source_snapshot(project)
        for project in build_species_archive_projects(species_name)
    )
