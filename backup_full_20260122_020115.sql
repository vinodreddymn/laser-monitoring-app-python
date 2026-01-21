/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.5-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: pneumatic_qc
-- ------------------------------------------------------
-- Server version	11.8.5-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Current Database: `pneumatic_qc`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `pneumatic_qc` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci */;

USE `pneumatic_qc`;

--
-- Table structure for table `alert_phones`
--

DROP TABLE IF EXISTS `alert_phones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `alert_phones` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `model_id` int(11) NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `model_id` (`model_id`),
  CONSTRAINT `alert_phones_ibfk_1` FOREIGN KEY (`model_id`) REFERENCES `models` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alert_phones`
--

LOCK TABLES `alert_phones` WRITE;
/*!40000 ALTER TABLE `alert_phones` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `alert_phones` VALUES
(44,18,'Ram','+919876543210'),
(45,18,'Krishna','+919876543210');
/*!40000 ALTER TABLE `alert_phones` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `cycle_print_log`
--

DROP TABLE IF EXISTS `cycle_print_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cycle_print_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cycle_id` int(11) NOT NULL,
  `print_type` enum('AUTO','MANUAL','REPRINT') NOT NULL,
  `printed_at` datetime DEFAULT current_timestamp(),
  `printed_by` varchar(50) DEFAULT NULL,
  `reason` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cycle_print_log_ibfk_1` (`cycle_id`),
  CONSTRAINT `cycle_print_log_ibfk_1` FOREIGN KEY (`cycle_id`) REFERENCES `cycles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=321 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cycle_print_log`
--

LOCK TABLES `cycle_print_log` WRITE;
/*!40000 ALTER TABLE `cycle_print_log` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `cycle_print_log` VALUES
(311,1733,'AUTO','2026-01-22 01:08:38','SYSTEM',NULL),
(312,1734,'AUTO','2026-01-22 01:10:00','SYSTEM',NULL),
(313,1735,'AUTO','2026-01-22 01:10:49','SYSTEM',NULL),
(314,1736,'AUTO','2026-01-22 01:11:25','SYSTEM',NULL),
(315,1737,'AUTO','2026-01-22 01:23:50','SYSTEM',NULL),
(316,1738,'AUTO','2026-01-22 01:35:34','SYSTEM',NULL),
(317,1739,'AUTO','2026-01-22 01:36:03','SYSTEM',NULL),
(318,1742,'AUTO','2026-01-22 01:37:40','SYSTEM',NULL),
(319,1745,'AUTO','2026-01-22 01:39:10','SYSTEM',NULL),
(320,1747,'AUTO','2026-01-22 01:40:27','SYSTEM',NULL);
/*!40000 ALTER TABLE `cycle_print_log` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `cycle_print_log_archive`
--

DROP TABLE IF EXISTS `cycle_print_log_archive`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cycle_print_log_archive` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `cycle_id` bigint(20) NOT NULL,
  `print_type` varchar(20) NOT NULL,
  `printed_at` datetime NOT NULL,
  `printed_by` varchar(50) DEFAULT NULL,
  `reason` text DEFAULT NULL,
  `archived_at` datetime NOT NULL,
  `purge_batch_id` varchar(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cycle` (`cycle_id`),
  KEY `idx_batch` (`purge_batch_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cycle_print_log_archive`
--

LOCK TABLES `cycle_print_log_archive` WRITE;
/*!40000 ALTER TABLE `cycle_print_log_archive` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `cycle_print_log_archive` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `cycles`
--

DROP TABLE IF EXISTS `cycles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cycles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` datetime DEFAULT NULL,
  `model_id` int(11) DEFAULT NULL,
  `model_name` varchar(100) DEFAULT NULL,
  `model_type` varchar(50) DEFAULT NULL,
  `peak_height` float DEFAULT NULL,
  `pass_fail` varchar(10) DEFAULT NULL,
  `qr_code` text DEFAULT NULL,
  `printed` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `model_id` (`model_id`),
  CONSTRAINT `cycles_ibfk_1` FOREIGN KEY (`model_id`) REFERENCES `models` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1753 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cycles`
--

LOCK TABLES `cycles` WRITE;
/*!40000 ALTER TABLE `cycles` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `cycles` VALUES
(1733,'2026-01-22 01:08:38',NULL,'Unknown','LHD',1.98,'PASS','G508.100005',1),
(1734,'2026-01-22 01:10:00',NULL,'Unknown','LHD',0.02,'PASS','G508.100006',1),
(1735,'2026-01-22 01:10:48',NULL,'Unknown','LHD',9.17,'PASS','G508.100007',1),
(1736,'2026-01-22 01:11:25',NULL,'Unknown','RHD',7.78,'PASS','G507.100008',1),
(1737,'2026-01-22 01:23:49',NULL,'Unknown','LHD',9,'PASS','G508.100009',1),
(1738,'2026-01-22 01:35:33',19,'G508','LHD',7.56,'PASS','G508.100010',1),
(1739,'2026-01-22 01:36:02',18,'G507','RHD',9,'PASS','G507.100010',1),
(1740,'2026-01-22 01:36:29',18,'G507','RHD',6.23,'FAIL',NULL,0),
(1741,'2026-01-22 01:37:05',18,'G507','RHD',6.87,'FAIL',NULL,0),
(1742,'2026-01-22 01:37:40',18,'G507','RHD',7.66,'PASS','G507.100011',1),
(1743,'2026-01-22 01:38:10',18,'G507','RHD',6.63,'FAIL',NULL,0),
(1744,'2026-01-22 01:38:38',18,'G507','RHD',5.77,'FAIL',NULL,0),
(1745,'2026-01-22 01:39:10',18,'G507','RHD',7.92,'PASS','G507.100012',1),
(1746,'2026-01-22 01:39:52',18,'G507','RHD',4.72,'FAIL',NULL,0),
(1747,'2026-01-22 01:40:27',18,'G507','RHD',7.3,'PASS','G507.100013',1),
(1748,'2026-01-22 01:42:25',18,'G507','RHD',9.13,'PASS','G507.100014',0),
(1749,'2026-01-22 01:42:52',18,'G507','RHD',5.11,'FAIL',NULL,0),
(1750,'2026-01-22 01:43:31',18,'G507','RHD',4.8,'FAIL',NULL,0),
(1751,'2026-01-22 01:43:59',18,'G507','RHD',7.57,'PASS','G507.100015',0),
(1752,'2026-01-22 01:44:49',18,'G507','RHD',9.06,'PASS','G507.100016',0);
/*!40000 ALTER TABLE `cycles` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `cycles_archive`
--

DROP TABLE IF EXISTS `cycles_archive`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cycles_archive` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL,
  `model_id` bigint(20) DEFAULT NULL,
  `model_name` varchar(100) NOT NULL,
  `model_type` varchar(50) NOT NULL,
  `peak_height` decimal(10,3) NOT NULL,
  `pass_fail` enum('PASS','FAIL') NOT NULL,
  `qr_code` varchar(255) DEFAULT NULL,
  `printed` tinyint(1) NOT NULL DEFAULT 0,
  `archived_at` datetime NOT NULL,
  `purge_batch_id` varchar(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ts` (`timestamp`),
  KEY `idx_qr` (`qr_code`),
  KEY `idx_batch` (`purge_batch_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cycles_archive`
--

LOCK TABLES `cycles_archive` WRITE;
/*!40000 ALTER TABLE `cycles_archive` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `cycles_archive` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `models`
--

DROP TABLE IF EXISTS `models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `models` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `model_type` varchar(10) DEFAULT NULL,
  `lower_limit` float DEFAULT NULL,
  `upper_limit` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `models`
--

LOCK TABLES `models` WRITE;
/*!40000 ALTER TABLE `models` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `models` VALUES
(18,'G507','RHD',7,10),
(19,'G508','LHD',7,9);
/*!40000 ALTER TABLE `models` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `qr_codes`
--

DROP TABLE IF EXISTS `qr_codes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `qr_codes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `qr_data` longtext DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `filename` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_created` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=1238 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `qr_codes`
--

LOCK TABLES `qr_codes` WRITE;
/*!40000 ALTER TABLE `qr_codes` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `qr_codes` VALUES
(1220,'G508.100000','2026-01-22 00:55:49','qr_images\\G508.100000.png'),
(1221,'G508.100001','2026-01-22 00:56:32','qr_images\\G508.100001.png'),
(1222,'G508.100002','2026-01-22 01:05:47','qr_images\\G508.100002.png'),
(1223,'G508.100003','2026-01-22 01:06:25','qr_images\\G508.100003.png'),
(1224,'G508.100004','2026-01-22 01:07:09','qr_images\\G508.100004.png'),
(1225,'G508.100005','2026-01-22 01:08:38','qr_images\\G508.100005.png'),
(1226,'G508.100006','2026-01-22 01:10:00','qr_images\\G508.100006.png'),
(1227,'G508.100007','2026-01-22 01:10:49','qr_images\\G508.100007.png'),
(1228,'G507.100008','2026-01-22 01:11:25','qr_images\\G507.100008.png'),
(1229,'G508.100009','2026-01-22 01:23:50','qr_images\\G508.100009.png'),
(1230,'G508.100010','2026-01-22 01:35:34','qr_images\\G508.100010.png'),
(1231,'G507.100010','2026-01-22 01:36:02','qr_images\\G507.100010.png'),
(1232,'G507.100011','2026-01-22 01:37:40','qr_images\\G507.100011.png'),
(1233,'G507.100012','2026-01-22 01:39:10','qr_images\\G507.100012.png'),
(1234,'G507.100013','2026-01-22 01:40:27','qr_images\\G507.100013.png'),
(1235,'G507.100014','2026-01-22 01:42:25','qr_images\\G507.100014.png'),
(1236,'G507.100015','2026-01-22 01:43:59','qr_images\\G507.100015.png'),
(1237,'G507.100016','2026-01-22 01:44:49','qr_images\\G507.100016.png');
/*!40000 ALTER TABLE `qr_codes` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `qr_codes_archive`
--

DROP TABLE IF EXISTS `qr_codes_archive`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `qr_codes_archive` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `qr_data` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL,
  `filename` varchar(255) NOT NULL,
  `archived_at` datetime NOT NULL,
  `purge_batch_id` varchar(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_qr` (`qr_data`),
  KEY `idx_batch` (`purge_batch_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `qr_codes_archive`
--

LOCK TABLES `qr_codes_archive` WRITE;
/*!40000 ALTER TABLE `qr_codes_archive` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `qr_codes_archive` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `sms_queue`
--

DROP TABLE IF EXISTS `sms_queue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sms_queue` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` datetime DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `message` text DEFAULT NULL,
  `status` enum('pending','sent','failed') DEFAULT 'pending',
  `retry_count` int(11) DEFAULT 0,
  `last_error` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=451 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sms_queue`
--

LOCK TABLES `sms_queue` WRITE;
/*!40000 ALTER TABLE `sms_queue` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `sms_queue` VALUES
(449,'2026-01-22 01:43:31','+919876543210','Ram','NTF QC Fail Alert: G507 (RHD) (7.00 - 10.00 mm) - Weld depth 4.80 mm on 22-01-2026 at 01:43:31. Info by ASHTECH','sent',0,NULL),
(450,'2026-01-22 01:43:31','+919876543210','Krishna','NTF QC Fail Alert: G507 (RHD) (7.00 - 10.00 mm) - Weld depth 4.80 mm on 22-01-2026 at 01:43:31. Info by ASHTECH','sent',0,NULL);
/*!40000 ALTER TABLE `sms_queue` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `sms_queue_archive`
--

DROP TABLE IF EXISTS `sms_queue_archive`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sms_queue_archive` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL,
  `phone` varchar(20) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `message` text NOT NULL,
  `status` varchar(20) NOT NULL,
  `retry_count` int(11) NOT NULL DEFAULT 0,
  `last_error` text DEFAULT NULL,
  `archived_at` datetime NOT NULL,
  `purge_batch_id` varchar(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ts` (`timestamp`),
  KEY `idx_phone` (`phone`),
  KEY `idx_batch` (`purge_batch_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sms_queue_archive`
--

LOCK TABLES `sms_queue_archive` WRITE;
/*!40000 ALTER TABLE `sms_queue_archive` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `sms_queue_archive` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `system_state`
--

DROP TABLE IF EXISTS `system_state`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_state` (
  `id` int(11) NOT NULL,
  `active_model_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `active_model_id` (`active_model_id`),
  CONSTRAINT `system_state_ibfk_1` FOREIGN KEY (`active_model_id`) REFERENCES `models` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_state`
--

LOCK TABLES `system_state` WRITE;
/*!40000 ALTER TABLE `system_state` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `system_state` VALUES
(1,18);
/*!40000 ALTER TABLE `system_state` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Dumping events for database 'pneumatic_qc'
--

--
-- Dumping routines for database 'pneumatic_qc'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-01-22  2:01:15
