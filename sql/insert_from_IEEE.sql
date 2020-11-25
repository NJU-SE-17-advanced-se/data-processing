insert ignore into data_processing.paper_reference (`pid`, `rid`) select r.pid, p.id
from data_processing_IEEE.paper_reference r, data_processing_IEEE.paper p
where r.r_doi = p.doi or r.r_document_id = p.id;
insert ignore into data_processing.affiliation select * from data_processing_IEEE.affiliation;
insert ignore into data_processing.domain select * from data_processing_IEEE.domain;
insert ignore into data_processing.paper select * from data_processing_IEEE.paper;
insert ignore into data_processing.paper_domain select * from data_processing_IEEE.paper_domain;
insert ignore into data_processing.paper_researcher select * from data_processing_IEEE.paper_researcher;
insert ignore into data_processing.publication select * from data_processing_IEEE.publication;
insert ignore into data_processing.researcher select * from data_processing_IEEE.researcher;
insert ignore into data_processing.researcher_affiliation select * from data_processing_IEEE.researcher_affiliation;