DROP DATABASE IF EXISTS data_processing;
CREATE DATABASE data_processing;
USE data_processing;

CREATE TABLE `paper` (
    `id` varchar(255) NOT NULL,
    `title` varchar(4095) COLLATE utf8_bin NOT NULL,
    `abs` varchar(8191) COLLATE utf8_bin NOT NULL,
    `publication_id` varchar(255) COLLATE utf8_bin NOT NULL,
    `publication_date` varchar(255) COLLATE utf8_bin NOT NULL,
    `link` varchar(255) COLLATE utf8_bin,
    `doi` varchar(255) COLLATE utf8_bin,
    `citation` int(11) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `domain` (
    `id` varchar(255) COLLATE utf8_bin NOT NULL,
    `name` varchar(255) COLLATE utf8_bin NOT NULL,
    `url` varchar(255) COLLATE utf8_bin,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `affiliation` (
    `id` varchar(255) NOT NULL,
    `name` varchar(255) COLLATE utf8_bin NOT NULL,
    `description` varchar(4095) COLLATE utf8_bin,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `publication` (
    `id` varchar(255) NOT NULL,
    `name` varchar(255) COLLATE utf8_bin NOT NULL,
    `publication_date` varchar(255) COLLATE utf8_bin NOT NULL,
    `impact` varchar(255) COLLATE utf8_bin DEFAULT '-1',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `researcher` (
    `id` varchar(255) NOT NULL,
    `name` varchar(255) COLLATE utf8_bin NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;


CREATE TABLE `paper_researcher` (
    `pid` varchar(255) COLLATE utf8_bin NOT NULL,
    `rid` varchar(255) COLLATE utf8_bin NOT NULL,
    `order` varchar(255) COLLATE utf8_bin NOT NULL,
    PRIMARY KEY (`pid`, `rid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `paper_reference` (
    `pid` varchar(255) COLLATE utf8_bin NOT NULL,
    `order` int(11) NOT NULL,
    `r_doi` varchar(255) COLLATE utf8_bin,
    `r_title` varchar(4095) COLLATE utf8_bin,
    `r_document_id` varchar(255) COLLATE utf8_bin,
    `r_citation` varchar(4095) COLLATE utf8_bin,
    PRIMARY KEY (`pid`, `order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `paper_domain` (
    `pid` varchar(255) COLLATE utf8_bin NOT NULL,
    `did` varchar(255) COLLATE utf8_bin NOT NULL,
    PRIMARY KEY (`pid`, `did`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `researcher_affiliation` (
    `rid` varchar(255) COLLATE utf8_bin NOT NULL,
    `aid` varchar(255) COLLATE utf8_bin NOT NULL,
    `year` varchar(255) COLLATE utf8_bin NOT NULL,
    PRIMARY KEY (`rid`, `aid`, `year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
