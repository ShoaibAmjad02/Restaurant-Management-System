-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: cafe
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `account_emailaddress`
--

DROP TABLE IF EXISTS `account_emailaddress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `account_emailaddress` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(254) NOT NULL,
  `verified` tinyint(1) NOT NULL,
  `primary` tinyint(1) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `account_emailaddress_user_id_email_987c8728_uniq` (`user_id`,`email`),
  KEY `account_emailaddress_email_03be32b2` (`email`),
  CONSTRAINT `account_emailaddress_user_id_2c513194_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `account_emailaddress`
--

LOCK TABLES `account_emailaddress` WRITE;
/*!40000 ALTER TABLE `account_emailaddress` DISABLE KEYS */;
/*!40000 ALTER TABLE `account_emailaddress` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `account_emailconfirmation`
--

DROP TABLE IF EXISTS `account_emailconfirmation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `account_emailconfirmation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `sent` datetime(6) DEFAULT NULL,
  `key` varchar(64) NOT NULL,
  `email_address_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  KEY `account_emailconfirm_email_address_id_5b7f8c58_fk_account_e` (`email_address_id`),
  CONSTRAINT `account_emailconfirm_email_address_id_5b7f8c58_fk_account_e` FOREIGN KEY (`email_address_id`) REFERENCES `account_emailaddress` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `account_emailconfirmation`
--

LOCK TABLES `account_emailconfirmation` WRITE;
/*!40000 ALTER TABLE `account_emailconfirmation` DISABLE KEYS */;
/*!40000 ALTER TABLE `account_emailconfirmation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=89 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add permission',1,'add_permission'),(2,'Can change permission',1,'change_permission'),(3,'Can delete permission',1,'delete_permission'),(4,'Can view permission',1,'view_permission'),(5,'Can add group',2,'add_group'),(6,'Can change group',2,'change_group'),(7,'Can delete group',2,'delete_group'),(8,'Can view group',2,'view_group'),(9,'Can add content type',3,'add_contenttype'),(10,'Can change content type',3,'change_contenttype'),(11,'Can delete content type',3,'delete_contenttype'),(12,'Can view content type',3,'view_contenttype'),(13,'Can add session',4,'add_session'),(14,'Can change session',4,'change_session'),(15,'Can delete session',4,'delete_session'),(16,'Can view session',4,'view_session'),(17,'Can add log entry',5,'add_logentry'),(18,'Can change log entry',5,'change_logentry'),(19,'Can delete log entry',5,'delete_logentry'),(20,'Can view log entry',5,'view_logentry'),(21,'Can add email address',6,'add_emailaddress'),(22,'Can change email address',6,'change_emailaddress'),(23,'Can delete email address',6,'delete_emailaddress'),(24,'Can view email address',6,'view_emailaddress'),(25,'Can add email confirmation',7,'add_emailconfirmation'),(26,'Can change email confirmation',7,'change_emailconfirmation'),(27,'Can delete email confirmation',7,'delete_emailconfirmation'),(28,'Can view email confirmation',7,'view_emailconfirmation'),(29,'Can add authenticator',8,'add_authenticator'),(30,'Can change authenticator',8,'change_authenticator'),(31,'Can delete authenticator',8,'delete_authenticator'),(32,'Can view authenticator',8,'view_authenticator'),(33,'Can add social account',9,'add_socialaccount'),(34,'Can change social account',9,'change_socialaccount'),(35,'Can delete social account',9,'delete_socialaccount'),(36,'Can view social account',9,'view_socialaccount'),(37,'Can add social application',10,'add_socialapp'),(38,'Can change social application',10,'change_socialapp'),(39,'Can delete social application',10,'delete_socialapp'),(40,'Can view social application',10,'view_socialapp'),(41,'Can add social application token',11,'add_socialtoken'),(42,'Can change social application token',11,'change_socialtoken'),(43,'Can delete social application token',11,'delete_socialtoken'),(44,'Can view social application token',11,'view_socialtoken'),(45,'Can add restaurant table',12,'add_restauranttable'),(46,'Can change restaurant table',12,'change_restauranttable'),(47,'Can delete restaurant table',12,'delete_restauranttable'),(48,'Can view restaurant table',12,'view_restauranttable'),(49,'Can add user',13,'add_user'),(50,'Can change user',13,'change_user'),(51,'Can delete user',13,'delete_user'),(52,'Can view user',13,'view_user'),(53,'Can add invoice',14,'add_invoice'),(54,'Can change invoice',14,'change_invoice'),(55,'Can delete invoice',14,'delete_invoice'),(56,'Can view invoice',14,'view_invoice'),(57,'Can add invoice item',15,'add_invoiceitem'),(58,'Can change invoice item',15,'change_invoiceitem'),(59,'Can delete invoice item',15,'delete_invoiceitem'),(60,'Can view invoice item',15,'view_invoiceitem'),(61,'Can add kitchen order',16,'add_kitchenorder'),(62,'Can change kitchen order',16,'change_kitchenorder'),(63,'Can delete kitchen order',16,'delete_kitchenorder'),(64,'Can view kitchen order',16,'view_kitchenorder'),(65,'Can add kitchen order item',17,'add_kitchenorderitem'),(66,'Can change kitchen order item',17,'change_kitchenorderitem'),(67,'Can delete kitchen order item',17,'delete_kitchenorderitem'),(68,'Can view kitchen order item',17,'view_kitchenorderitem'),(69,'Can add category',18,'add_category'),(70,'Can change category',18,'change_category'),(71,'Can delete category',18,'delete_category'),(72,'Can view category',18,'view_category'),(73,'Can add food',19,'add_food'),(74,'Can change food',19,'change_food'),(75,'Can delete food',19,'delete_food'),(76,'Can view food',19,'view_food'),(77,'Can add cart',20,'add_cart'),(78,'Can change cart',20,'change_cart'),(79,'Can delete cart',20,'delete_cart'),(80,'Can view cart',20,'view_cart'),(81,'Can add order',21,'add_order'),(82,'Can change order',21,'change_order'),(83,'Can delete order',21,'delete_order'),(84,'Can view order',21,'view_order'),(85,'Can add order item',22,'add_orderitem'),(86,'Can change order item',22,'change_orderitem'),(87,'Can delete order item',22,'delete_orderitem'),(88,'Can view order item',22,'view_orderitem');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_users_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (6,'account','emailaddress'),(7,'account','emailconfirmation'),(5,'admin','logentry'),(2,'auth','group'),(1,'auth','permission'),(3,'contenttypes','contenttype'),(18,'menu','category'),(19,'menu','food'),(8,'mfa','authenticator'),(20,'orders','cart'),(21,'orders','order'),(22,'orders','orderitem'),(4,'sessions','session'),(9,'socialaccount','socialaccount'),(10,'socialaccount','socialapp'),(11,'socialaccount','socialtoken'),(14,'users','invoice'),(15,'users','invoiceitem'),(16,'users','kitchenorder'),(17,'users','kitchenorderitem'),(12,'users','restauranttable'),(13,'users','user');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=48 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-06-19 18:07:39.152963'),(2,'contenttypes','0002_remove_content_type_name','2026-06-19 18:07:39.305157'),(3,'auth','0001_initial','2026-06-19 18:07:39.804356'),(4,'auth','0002_alter_permission_name_max_length','2026-06-19 18:07:39.909404'),(5,'auth','0003_alter_user_email_max_length','2026-06-19 18:07:39.909404'),(6,'auth','0004_alter_user_username_opts','2026-06-19 18:07:39.930139'),(7,'auth','0005_alter_user_last_login_null','2026-06-19 18:07:39.936422'),(8,'auth','0006_require_contenttypes_0002','2026-06-19 18:07:39.944603'),(9,'auth','0007_alter_validators_add_error_messages','2026-06-19 18:07:39.954581'),(10,'auth','0008_alter_user_username_max_length','2026-06-19 18:07:39.963967'),(11,'auth','0009_alter_user_last_name_max_length','2026-06-19 18:07:39.971490'),(12,'auth','0010_alter_group_name_max_length','2026-06-19 18:07:40.001264'),(13,'auth','0011_update_proxy_permissions','2026-06-19 18:07:40.012286'),(14,'auth','0012_alter_user_first_name_max_length','2026-06-19 18:07:40.018677'),(15,'users','0001_initial','2026-06-19 18:07:41.592556'),(16,'account','0001_initial','2026-06-19 18:07:41.938960'),(17,'account','0002_email_max_length','2026-06-19 18:07:41.973850'),(18,'account','0003_alter_emailaddress_create_unique_verified_email','2026-06-19 18:07:42.036276'),(19,'account','0004_alter_emailaddress_drop_unique_email','2026-06-19 18:07:42.104378'),(20,'account','0005_emailaddress_idx_upper_email','2026-06-19 18:07:42.163279'),(21,'account','0006_emailaddress_lower','2026-06-19 18:07:42.188245'),(22,'account','0007_emailaddress_idx_email','2026-06-19 18:07:42.306556'),(23,'account','0008_emailaddress_unique_primary_email_fixup','2026-06-19 18:07:42.335477'),(24,'account','0009_emailaddress_unique_primary_email','2026-06-19 18:07:42.349362'),(25,'admin','0001_initial','2026-06-19 18:07:42.603514'),(26,'admin','0002_logentry_remove_auto_add','2026-06-19 18:07:42.612206'),(27,'admin','0003_logentry_add_action_flag_choices','2026-06-19 18:07:42.644039'),(28,'menu','0001_initial','2026-06-19 18:07:42.776767'),(29,'menu','0002_food_created_at_food_updated_at_alter_food_category_and_more','2026-06-19 18:07:43.037485'),(30,'mfa','0001_initial','2026-06-19 18:07:43.193933'),(31,'mfa','0002_authenticator_timestamps','2026-06-19 18:07:43.376843'),(32,'mfa','0003_authenticator_type_uniq','2026-06-19 18:07:43.512907'),(33,'orders','0001_initial','2026-06-19 18:07:44.135432'),(34,'sessions','0001_initial','2026-06-19 18:07:44.195356'),(35,'socialaccount','0001_initial','2026-06-19 18:07:44.664485'),(36,'socialaccount','0002_token_max_lengths','2026-06-19 18:07:44.749126'),(37,'socialaccount','0003_extra_data_default_dict','2026-06-19 18:07:44.771425'),(38,'socialaccount','0004_app_provider_id_settings','2026-06-19 18:07:45.026835'),(39,'socialaccount','0005_socialtoken_nullable_app','2026-06-19 18:07:45.285953'),(40,'socialaccount','0006_alter_socialaccount_extra_data','2026-06-19 18:07:45.405096'),(41,'users','0002_inventory_removal','2026-06-19 18:07:46.032664'),(42,'users','0003_invoice_qr_code_image','2026-06-19 18:07:46.141359'),(43,'menu','0003_seed_categories','2026-06-20 00:02:46.375262'),(44,'users','0004_invoice_payment_method_invoice_subtotal_amount_and_more','2026-06-20 05:27:20.272120'),(45,'users','0005_user_timezone','2026-06-21 01:56:22.445457'),(46,'users','0006_add_customer_timezone','2026-06-21 02:54:39.724986'),(47,'users','0007_change_user_timezone_default_to_utc','2026-06-21 03:20:38.193457');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('287bbtl53igetw3pno63ac21vtdcihxd','.eJxVjMEOwiAQRP-FsyHLgtB69N5vaJZllaqBpLQn47_bJj3oYS7z3sxbjbQueVybzOOU1EVZdfrtIvFTyg7Sg8q9aq5lmaeod0UftOmhJnldD_fvIFPL25p7cNZhROx8YLL-JhisOOghxjMJMCTjAR0yGrGdAesxGpAtHgKrzxe-NDar:1wae5x:UAiV03cd1S8k2yW8x_EufqEFtdmK8pRJ8CvjvFji9Zc','2026-07-03 18:37:37.972782'),('crfke6ir3jhry3hknfimtr8e14ph129h','eyJ0YWJsZV9ubyI6MywidGFibGVfdG9rZW4iOiJVSFR3TFQyb1dyOUd6WTdXSnBjZERqZ0J6OW85WWRqciIsImN1c3RvbWVyX3Nlc3Npb25faWQiOiJlNGY2OGU2MC04MzU3LTQzZWItOTEzZS02YjcyOTg2MTUyNzMifQ:1wajYQ:xN2lb66a7Qskt2_yx4p5bkqvXJFAFJchEw20QouPpQ0','2026-07-04 00:27:22.521378'),('koacdqz9r1yi9c9q6kwxylgmtimtgeew','.eJxVjMESgiAURf-FdWMpiNLO1vUNzOPxUEphRnRT078njYva3nPPeTEN6zLoNdGsvWVnVrHD72YAHxQysHcIfSwwhmX2psiXYqepuEVL42X__gUGSEO2ESulXCmMI64QpSoF1bU0tnWNMA1ZzjkoAShaB9Y55ThJlJay0Jy26De3-ImeMdCW7CaaPcLxGpPuQk8jJfb-AJ7XRxg:1wb8vg:0VWqkwqEFPrH7bTCaTZY6cRQ8412f65W0cAWcY50xTQ','2026-07-05 03:33:04.410790'),('ok2ebj01sd92l0oelu6rn4q1cd4pcr8s','.eJxVjLsSgjAURP8ltYM3DwPaYa3fkElurhCFZIZAo-O_GxwKLbbZPXtezNhl7s2SaTLBsxOTbPfbOYsPiuvg7zZ2qcIU5ym4akWqbc3VNXkazhv7J-ht7ssbj6CkEk6IRtdopb6RqCUpOIJzB0uA4LkGoQQKTrLhILVwHKhEQ41F-tXNYaRnilSU7UhTQLu_pGza2NFAmb0_4R5ETw:1wb99R:TnErVo1eaJjh-v6z2u4pnTWCjB7vVeFVLJIMarX2BnE','2026-07-05 03:47:17.267891'),('q45z2ae67r59g46oa3r034jhd5ej8r7d','.eJxVjMEOwiAQRP-FsyHQLpR69N5vIAu7SNVAUtqT8d9tkx70Npn3Zt7C47ZmvzVe_EziKrS4_HYB45PLAeiB5V5lrGVd5iAPRZ60yakSv26n-3eQseV9PZAdQQMFxJh6AxgVuZETYwJn9Z46O0DfK1A6BGuhQ2ClyEByaLQSny_zrjfE:1wamoJ:GhZK2Io7xMj94wFlP3vPoi6oYAiTfiE-qMDevKvzbaQ','2026-07-04 03:55:59.356378'),('qfsvvatryty4xd2hjek3xinlzmyzxkaf','.eJxVj09PwzAMxb9LzrQkjZO2u21cpk0gAYJr5fwpzdYmUpMKbYjvTgbjsJvt93vP9hdZop275CZ7Dt6SFVlHh_d7nFEPjtyRDpc0dL-QM1lmtzOF-mj9RTAH9B-h1MGn2anygpRXNZaPwdhxc2VvAgaMQ3bXRrbAwChE3XMBqKlpWttb7KGRLFeVrIFzCpQpJSVUCJZSI6BvUDCaQxOq0XY-kFX136SQF-b058-nxNULxu3bafR7t3sQy3nqj6_bzUnG4T279RJTmPJB0cbogv_7VgMFUVNT1KaiBaiGFUpIVjCutKi4gZbV5PsH1ORpWg:1wb8Ot:lIx-r7FLRTBK6qZrMG1CTb2ytc2ASXPlvXznzNm8Xq0','2026-07-05 02:59:11.493968'),('rqh1wjc1ei4yljmqbkjpy1b0ctsxssp7','eyJ1c2VyX3RpbWV6b25lIjoiQW1lcmljYS9Mb3NfQW5nZWxlcyJ9:1wb92Q:CpWgVo0O4qixyzDuymklSIyqCdtPMPemH1J5eesEFZM','2026-07-05 03:40:02.603019'),('uzhacbhid42l15f7tg0nb1ndmfdy55vh','.eJxVjM0OwiAQhN-Fs0GwW9p606vxGZqFXQR_ICntReO725peepvM9818xFR46Mf44ndOLI7iVCLuLzigC1HsRI_TGPq_FGnGettZdA9OC6A7pluWLqdxiFYuilxpkddM_Dyv7uYgYAnzuiHTgQayiM5XNaBT1HbsGT20Rs_pYBqoKgVKW2sMHBBYKarBt1hrJb4_65VCmw:1wb8n0:eeOdRgY1U2un59GOVHWWi1suPUVCi5QiZR1TbWjaN4E','2026-07-05 03:24:06.355998'),('xtf73oh70wppnq23h59vh8z1fy5nvpd9','.eJxVjsFOwzAQRP_FZxLs2HHc3louFRVIgOAare01MU1sKXaEWsS_41bl0Nvuzryd-SFLwrnPfsJTDEjWZJM83O9hBjN4ckcy6BH7EMm6-V9yPGAozpfv58z1K6Td-3EMe__40C6nyR3edtujTMNHoc2ScpxKQMKUfAy9twXExjRqxbtKoJKVYMZUAGAq1ilhWucccCxwD0se-ku_C8ZubxpM6XEW7BeEz1ibGPLsdX221Fc11U_R4ri9em8eDJCGQndWrgQTVpcKjrcCDLVqhQ7BCSVZmRrZCc6poExrKUUDAim1rXAKWkbJ7x8mXWq_:1wb8YU:kFcB8DUeHL4DiNZ5E3C_70UzC05sRhBMYnYD9c-2nI0','2026-07-05 03:09:06.742726'),('y6ogiw7s691b72nfuzkjnstcesgh0n9j','.eJw1zLsOgjAUgOF36WwjUOS2ERITbzFx0a2p5RQaSxs5RVHju9vF8R--_0MmhJF7PcDbWSAVqQcYtRTLvUNe2w4MIFkQL64GuHWkiv_h3Q1sAKzZ9NnhuPXDnSUnZuZ511988zLPM3uMaxW0nNC78OUIiNpZrtsAy1YWGSQRjQpgNM1LRYtVqiioMhJ5LGQqgHx_2No1wQ:1wbADF:azrLzh-NGM0OvHYy4PQlP7NmucTL65zyozvgwCxHeJA','2026-07-05 04:55:17.264777');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `menu_category`
--

DROP TABLE IF EXISTS `menu_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `menu_category` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `menu_category`
--

LOCK TABLES `menu_category` WRITE;
/*!40000 ALTER TABLE `menu_category` DISABLE KEYS */;
INSERT INTO `menu_category` VALUES (1,'Fast Food'),(2,'Drinks'),(3,'Desserts'),(4,'Burger'),(5,'Pizza'),(6,'BBQ'),(7,'Sandwich'),(8,'Chinese');
/*!40000 ALTER TABLE `menu_category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `menu_food`
--

DROP TABLE IF EXISTS `menu_food`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `menu_food` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `image` varchar(100) DEFAULT NULL,
  `available` tinyint(1) NOT NULL,
  `category_id` bigint NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `menu_food_category_id_39589c01_fk_menu_category_id` (`category_id`),
  CONSTRAINT `menu_food_category_id_39589c01_fk_menu_category_id` FOREIGN KEY (`category_id`) REFERENCES `menu_category` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `menu_food`
--

LOCK TABLES `menu_food` WRITE;
/*!40000 ALTER TABLE `menu_food` DISABLE KEYS */;
INSERT INTO `menu_food` VALUES (1,'Burger','Very tasty burger',500.00,'',1,1,'2026-06-19 18:21:24.803616','2026-06-19 18:21:24.803616'),(2,'Apple Juice','Tasty Juice',1500.00,'',1,2,'2026-06-19 18:22:15.919910','2026-06-19 23:46:37.059343'),(3,'Fish','1kg fried',1950.00,'',1,3,'2026-06-19 18:23:01.235797','2026-06-19 18:23:01.235797');
/*!40000 ALTER TABLE `menu_food` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mfa_authenticator`
--

DROP TABLE IF EXISTS `mfa_authenticator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mfa_authenticator` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `data` json NOT NULL,
  `user_id` bigint NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `last_used_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `mfa_authenticator_user_id_0c3a50c0` (`user_id`),
  CONSTRAINT `mfa_authenticator_user_id_0c3a50c0_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mfa_authenticator`
--

LOCK TABLES `mfa_authenticator` WRITE;
/*!40000 ALTER TABLE `mfa_authenticator` DISABLE KEYS */;
/*!40000 ALTER TABLE `mfa_authenticator` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders_cart`
--

DROP TABLE IF EXISTS `orders_cart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders_cart` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `food_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `orders_cart_food_id_ad92e664_fk_menu_food_id` (`food_id`),
  KEY `orders_cart_user_id_121a069e_fk_users_user_id` (`user_id`),
  CONSTRAINT `orders_cart_food_id_ad92e664_fk_menu_food_id` FOREIGN KEY (`food_id`) REFERENCES `menu_food` (`id`),
  CONSTRAINT `orders_cart_user_id_121a069e_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`),
  CONSTRAINT `orders_cart_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders_cart`
--

LOCK TABLES `orders_cart` WRITE;
/*!40000 ALTER TABLE `orders_cart` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders_cart` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders_order`
--

DROP TABLE IF EXISTS `orders_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders_order` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `total_amount` decimal(10,2) NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `orders_order_user_id_e9b59eb1_fk_users_user_id` (`user_id`),
  CONSTRAINT `orders_order_user_id_e9b59eb1_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders_order`
--

LOCK TABLES `orders_order` WRITE;
/*!40000 ALTER TABLE `orders_order` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders_order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders_orderitem`
--

DROP TABLE IF EXISTS `orders_orderitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders_orderitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int unsigned NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `food_id` bigint NOT NULL,
  `order_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `orders_orderitem_food_id_25867428_fk_menu_food_id` (`food_id`),
  KEY `orders_orderitem_order_id_fe61a34d_fk_orders_order_id` (`order_id`),
  CONSTRAINT `orders_orderitem_food_id_25867428_fk_menu_food_id` FOREIGN KEY (`food_id`) REFERENCES `menu_food` (`id`),
  CONSTRAINT `orders_orderitem_order_id_fe61a34d_fk_orders_order_id` FOREIGN KEY (`order_id`) REFERENCES `orders_order` (`id`),
  CONSTRAINT `orders_orderitem_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders_orderitem`
--

LOCK TABLES `orders_orderitem` WRITE;
/*!40000 ALTER TABLE `orders_orderitem` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders_orderitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `socialaccount_socialaccount`
--

DROP TABLE IF EXISTS `socialaccount_socialaccount`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `socialaccount_socialaccount` (
  `id` int NOT NULL AUTO_INCREMENT,
  `provider` varchar(200) NOT NULL,
  `uid` varchar(191) NOT NULL,
  `last_login` datetime(6) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `extra_data` json NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `socialaccount_socialaccount_provider_uid_fc810c6e_uniq` (`provider`,`uid`),
  KEY `socialaccount_socialaccount_user_id_8146e70c_fk_users_user_id` (`user_id`),
  CONSTRAINT `socialaccount_socialaccount_user_id_8146e70c_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `socialaccount_socialaccount`
--

LOCK TABLES `socialaccount_socialaccount` WRITE;
/*!40000 ALTER TABLE `socialaccount_socialaccount` DISABLE KEYS */;
/*!40000 ALTER TABLE `socialaccount_socialaccount` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `socialaccount_socialapp`
--

DROP TABLE IF EXISTS `socialaccount_socialapp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `socialaccount_socialapp` (
  `id` int NOT NULL AUTO_INCREMENT,
  `provider` varchar(30) NOT NULL,
  `name` varchar(40) NOT NULL,
  `client_id` varchar(191) NOT NULL,
  `secret` varchar(191) NOT NULL,
  `key` varchar(191) NOT NULL,
  `provider_id` varchar(200) NOT NULL,
  `settings` json NOT NULL DEFAULT (_utf8mb3'{}'),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `socialaccount_socialapp`
--

LOCK TABLES `socialaccount_socialapp` WRITE;
/*!40000 ALTER TABLE `socialaccount_socialapp` DISABLE KEYS */;
/*!40000 ALTER TABLE `socialaccount_socialapp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `socialaccount_socialtoken`
--

DROP TABLE IF EXISTS `socialaccount_socialtoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `socialaccount_socialtoken` (
  `id` int NOT NULL AUTO_INCREMENT,
  `token` longtext NOT NULL,
  `token_secret` longtext NOT NULL,
  `expires_at` datetime(6) DEFAULT NULL,
  `account_id` int NOT NULL,
  `app_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `socialaccount_socialtoken_app_id_account_id_fca4e0ac_uniq` (`app_id`,`account_id`),
  KEY `socialaccount_social_account_id_951f210e_fk_socialacc` (`account_id`),
  CONSTRAINT `socialaccount_social_account_id_951f210e_fk_socialacc` FOREIGN KEY (`account_id`) REFERENCES `socialaccount_socialaccount` (`id`),
  CONSTRAINT `socialaccount_social_app_id_636a42d7_fk_socialacc` FOREIGN KEY (`app_id`) REFERENCES `socialaccount_socialapp` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `socialaccount_socialtoken`
--

LOCK TABLES `socialaccount_socialtoken` WRITE;
/*!40000 ALTER TABLE `socialaccount_socialtoken` DISABLE KEYS */;
/*!40000 ALTER TABLE `socialaccount_socialtoken` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_invoice`
--

DROP TABLE IF EXISTS `users_invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_invoice` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `customer_name` varchar(255) DEFAULT NULL,
  `customer_email` varchar(254) DEFAULT NULL,
  `table_no` int DEFAULT NULL,
  `customer_session_id` varchar(100) DEFAULT NULL,
  `invoice_number` varchar(50) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` bigint DEFAULT NULL,
  `uuid_token` varchar(64) NOT NULL,
  `qr_code_image` varchar(100) DEFAULT NULL,
  `payment_method` varchar(20) DEFAULT NULL,
  `subtotal_amount` decimal(10,2) NOT NULL,
  `tax_amount` decimal(10,2) NOT NULL,
  `tax_percentage` decimal(5,2) NOT NULL,
  `customer_timezone` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `invoice_number` (`invoice_number`),
  UNIQUE KEY `users_invoice_uuid_token_1e6e2616_uniq` (`uuid_token`),
  KEY `users_invoice_user_id_9574df2b_fk_users_user_id` (`user_id`),
  CONSTRAINT `users_invoice_user_id_9574df2b_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_invoice`
--

LOCK TABLES `users_invoice` WRITE;
/*!40000 ALTER TABLE `users_invoice` DISABLE KEYS */;
INSERT INTO `users_invoice` VALUES (1,NULL,NULL,NULL,'eab37d2c-8c4d-4556-8efb-cf7ca1686349','INV-F3542B59',2000.00,'2026-06-19 18:24:46.104620',2,'aff1a700f2af4719bf3ebfd1fd38a20f','invoice_qrcodes/invoice_INV-F3542B59_qr_4uZ3qMn.png',NULL,0.00,0.00,0.00,'UTC'),(2,NULL,NULL,3,'16c41b98-8dbe-4b8c-8404-4227fe6e3972','INV-10D5B70D',3950.00,'2026-06-19 18:36:41.301219',NULL,'cc199ea996504441b280e5ea3b7605e1','invoice_qrcodes/invoice_INV-10D5B70D_qr_GhyxHJC.png',NULL,0.00,0.00,0.00,'UTC'),(3,NULL,NULL,NULL,'04fdc11a-151c-46f6-965b-da936bb83372','INV-B867ACCD',4400.00,'2026-06-19 23:10:30.013885',2,'e67db302f1e4402f955ea06d3b5cd663','invoice_qrcodes/invoice_INV-B867ACCD_qr_wAHrzWK.png',NULL,0.00,0.00,0.00,'UTC'),(4,NULL,NULL,NULL,'6bb98056-a0f9-4a2f-bc80-ebeada1617db','INV-3795A8C8',7450.00,'2026-06-19 23:49:20.426152',NULL,'90248fb6fbf64e5eae92c57bea66099d','invoice_qrcodes/invoice_INV-3795A8C8_qr_xUHEBk2.png',NULL,0.00,0.00,0.00,'UTC'),(5,NULL,NULL,3,'2b3ac48b-9bbe-410e-ae62-dd1639630ff8','INV-7B8A78BB',2000.00,'2026-06-19 23:50:15.801992',NULL,'2856929a026f4809a8568827d9d6d091','invoice_qrcodes/invoice_INV-7B8A78BB_qr_FchQSzd.png',NULL,0.00,0.00,0.00,'UTC'),(6,NULL,NULL,NULL,'705c40cc-907d-4844-9b80-3020648ea8d4','INV-3BD1741C',9850.00,'2026-06-20 04:04:30.087632',2,'67b03c72ff2245ab85a8c47592fe04a0','invoice_qrcodes/invoice_INV-3BD1741C_qr_H9z4JtN.png',NULL,0.00,0.00,0.00,'UTC'),(7,NULL,NULL,NULL,'44c1bc43-f532-4ca2-8800-5b8c1b0e08c1','INV-80F1FBF0',5251.00,'2026-06-20 05:29:09.832515',2,'3b5e56bcf5bf4222a7185f056a70b1ab','invoice_qrcodes/invoice_INV-80F1FBF0_qr_xvLnH2D.png','cash',4450.00,801.00,18.00,'UTC'),(8,NULL,NULL,NULL,'0a5812c7-d5d0-441b-b113-c6cc0be6be33','INV-9EE76A6E',4672.50,'2026-06-20 05:29:24.793917',2,'e491d5181cc046fba67a242650ccc868','invoice_qrcodes/invoice_INV-9EE76A6E_qr_pojCYmW.png','card',4450.00,222.50,5.00,'UTC'),(9,NULL,NULL,NULL,'22da0d84-2227-4890-8dd3-be5f887a3f9f','INV-AAEFFC01',5251.00,'2026-06-20 05:34:10.348026',2,'a631530c8b0048e689599567545d21bc','invoice_qrcodes/invoice_INV-AAEFFC01_qr_vqc9k5y.png','cash',4450.00,801.00,18.00,'UTC'),(10,NULL,NULL,NULL,'2939ae45-be95-4446-b6ea-1b1c99f5daa4','INV-FFBB40FB',4071.00,'2026-06-20 05:39:42.552330',2,'9493ba56f2f543729a0f865c52e8e0a7','invoice_qrcodes/invoice_INV-FFBB40FB_qr_ySbj3SM.png','cash',3450.00,621.00,18.00,'UTC'),(11,NULL,NULL,1,'60325e95-63ae-4802-a55b-3318653a7184','INV-224F88C5',2625.00,'2026-06-20 05:49:01.126087',NULL,'685414d363c34f9280b9da818ad8a6da','invoice_qrcodes/invoice_INV-224F88C5_qr_5OQfNkZ.png','card',2500.00,125.00,5.00,'UTC'),(12,NULL,NULL,NULL,'249f3a7c-be14-456f-8825-9c7d95674199','INV-55149782',3675.00,'2026-06-21 01:59:31.337644',2,'47adcae0fc1b4bb5b3ed54a71da4edf0','invoice_qrcodes/invoice_INV-55149782_qr_T43zg2f.png','card',3500.00,175.00,5.00,'UTC'),(13,NULL,NULL,NULL,'a784b117-1790-413c-9b32-e41916dbb335','INV-DA4C0500',2360.00,'2026-06-21 02:10:31.110971',2,'f0bc02062ac14e5d8f8cbe47118f3d3a','invoice_qrcodes/invoice_INV-DA4C0500_qr_TlcELVd.png','cash',2000.00,360.00,18.00,'UTC'),(14,NULL,NULL,NULL,'60ba570d-3a06-456d-b726-9b6711da2920','INV-573EC949',4147.50,'2026-06-21 02:57:42.891996',2,'5c5f32dffbdf4b5f8bf13393519f1823','invoice_qrcodes/invoice_INV-573EC949_qr_vn3kSlx.png','card',3950.00,197.50,5.00,'America/Los_Angeles'),(15,NULL,NULL,NULL,'ef4759f7-c016-4008-aa17-07c0f2d16be6','INV-619F69B0',6142.50,'2026-06-21 03:03:24.815074',6,'6680d81c53fb4147854959f8ea6212ac','invoice_qrcodes/invoice_INV-619F69B0_qr_UpDSBbV.png','card',5850.00,292.50,5.00,'America/Los_Angeles'),(16,NULL,NULL,NULL,'beb0562b-d324-469c-9f84-884c8a0047f3','INV-8E8DF349',2100.00,'2026-06-21 03:15:48.152562',6,'ee42108c541c4fd3b0b246e84d357449','invoice_qrcodes/invoice_INV-8E8DF349_qr_KFB3jtM.png','card',2000.00,100.00,5.00,'America/Los_Angeles'),(17,NULL,NULL,NULL,'57a511f3-a21e-433c-b1d4-86c01cc15a7e','INV-0D571A6E',2100.00,'2026-06-21 03:22:43.718167',2,'b12d5236b1ec462caddb0848c5deabb2','invoice_qrcodes/invoice_INV-0D571A6E_qr_ixisYCa.png','card',2000.00,100.00,5.00,'America/Los_Angeles'),(18,NULL,NULL,NULL,'20db7b4a-2302-48f7-94ec-6ae40bf80cf8','INV-E07FC9CC',3622.50,'2026-06-21 03:27:16.996358',2,'3c59e46dc47c4f41a5b16d74475b2acd','invoice_qrcodes/invoice_INV-E07FC9CC_qr_qCaiT62.png','card',3450.00,172.50,5.00,'America/Los_Angeles'),(19,NULL,NULL,NULL,'f5c9c22d-ac98-4bff-bfbd-f51f909aba7c','INV-42CB116C',2100.00,'2026-06-21 03:30:42.213247',2,'90cf3feadca44448ba3680532a62298e','invoice_qrcodes/invoice_INV-42CB116C_qr_sDaYKt2.png','card',2000.00,100.00,5.00,'America/Los_Angeles'),(20,NULL,NULL,NULL,'f27a348d-389b-469e-8457-a0f6a0808c7b','INV-AF99173A',2047.50,'2026-06-21 03:41:50.015412',2,'b554fba326c44b7e9fedbfdbe3b2bb0a','invoice_qrcodes/invoice_INV-AF99173A_qr_t7FIC0j.png','card',1950.00,97.50,5.00,'America/Los_Angeles'),(21,NULL,NULL,NULL,'33f9ca5a-a2bb-4ba7-8b7f-00b3e7c495c2','INV-B934D109',2301.00,'2026-06-21 03:51:16.337974',2,'63833807309540279836592a139d7a4b','invoice_qrcodes/invoice_INV-B934D109_qr_s2sv8EI.png','cash',1950.00,351.00,18.00,'America/Los_Angeles'),(22,NULL,NULL,NULL,'052009d4-494c-4050-8f7f-e8cc917b961a','INV-333CE94D',525.00,'2026-06-21 03:53:47.675050',2,'55400d6927ff405d966bbf398758371d','invoice_qrcodes/invoice_INV-333CE94D_qr_SCMIY5Z.png','card',500.00,25.00,5.00,'America/Los_Angeles'),(23,NULL,NULL,1,'9dc86e20-08e3-479f-854f-ef90a71ac4ae','INV-508B314A',2301.00,'2026-06-21 04:03:47.098793',NULL,'8d8e2159af704a0f8e2d1843676a346a','invoice_qrcodes/invoice_INV-508B314A_qr_ZXS3ci4.png','cash',1950.00,351.00,18.00,'America/Los_Angeles'),(24,NULL,NULL,NULL,'7e445fa6-2d01-43c5-9f68-b5feec3ffcdf','INV-9FF2A463',3675.00,'2026-06-21 04:57:28.209065',2,'35fa318b6d57454c8d7339be8a345e3a','invoice_qrcodes/invoice_INV-9FF2A463_qr_yrgtqbo.png','card',3500.00,175.00,5.00,'America/Los_Angeles'),(25,NULL,NULL,NULL,'8fb864c9-6d0b-4268-8533-60ba9a2b8985','INV-477AA181',2047.50,'2026-06-21 12:25:23.179164',2,'e0dd94b3630d4fcaa3a602c68ac7b304','invoice_qrcodes/invoice_INV-477AA181_qr_3zzBpVk.png','card',1950.00,97.50,5.00,'America/Los_Angeles'),(26,NULL,NULL,NULL,'13d26a10-87a7-4d18-92fe-e0bcb121feb5','INV-BDFE6173',525.00,'2026-06-21 12:26:45.335064',2,'676d629d78714585b02db76f468fcb95','invoice_qrcodes/invoice_INV-BDFE6173_qr_njuRq8o.png','card',500.00,25.00,5.00,'America/Los_Angeles'),(27,NULL,NULL,NULL,'53bf8fa4-7878-485f-b388-44a751fe18fd','INV-C0C1E7D3',1575.00,'2026-06-21 13:29:15.876382',2,'3dacf9ea03ba49c7a1de1c581f5cb3e7','invoice_qrcodes/invoice_INV-C0C1E7D3_qr_AS0ukwf.png','card',1500.00,75.00,5.00,'Asia/Karachi'),(28,NULL,NULL,NULL,'c986ce3d-cc2b-44e7-8f58-77ec16f7d3f0','INV-2AAD632A',590.00,'2026-06-21 02:01:15.656013',2,'99f12909118541e7898b97190f7edc30','invoice_qrcodes/invoice_INV-2AAD632A_qr_51kZyyu.png','cash',500.00,90.00,18.00,'Asia/Karachi'),(29,NULL,NULL,NULL,'0ddea72a-c34b-4081-b0a1-2ccfa1b25ef4','INV-B1A89224',2047.50,'2026-06-21 02:09:03.732327',2,'a9f99473fd884be0bfcc119140fd2e4b','invoice_qrcodes/invoice_INV-B1A89224_qr_WDuTuLK.png','card',1950.00,97.50,5.00,'Asia/Karachi'),(30,NULL,NULL,NULL,'1fa18761-2e49-4071-b270-b0fcc9fa7c6b','INV-DFF3ECA4',1770.00,'2026-06-21 02:12:49.120962',2,'7b59c4e1b91646bb8647d037cc3e0386','invoice_qrcodes/invoice_INV-DFF3ECA4_qr_n1WEQjp.png','cash',1500.00,270.00,18.00,'Asia/Karachi'),(31,NULL,NULL,NULL,'a21f0137-707c-4dce-acf3-3ed0e6f52093','INV-244E8361',525.00,'2026-06-21 02:17:10.018157',2,'e34a668628df413a82f3a5e6b65572cc','invoice_qrcodes/invoice_INV-244E8361_qr_N8BYysL.png','card',500.00,25.00,5.00,'Asia/Karachi'),(32,NULL,NULL,NULL,'39eb7952-dc86-4bdb-b66d-b707cb16b1f8','INV-34A66AC1',2100.00,'2026-06-21 02:18:06.764637',2,'4c0b2438990d4aca9c786116e2877c6e','invoice_qrcodes/invoice_INV-34A66AC1_qr_IR5A1T2.png','card',2000.00,100.00,5.00,'Asia/Karachi'),(33,NULL,NULL,NULL,'962d073c-fd86-4139-9782-9d912599ce1c','INV-B7408173',525.00,'2026-06-21 02:18:55.221988',2,'eff27a83c90e40eaae89c2fcf2f9c086','invoice_qrcodes/invoice_INV-B7408173_qr_BVLv94A.png','card',500.00,25.00,5.00,'Asia/Karachi'),(34,NULL,NULL,NULL,'e6e79430-72ae-4d53-ba6c-ea698492db38','INV-C0A3749F',2100.00,'2026-06-21 02:26:46.296025',2,'c6f75eb8264347ff840334f22fb48e13','invoice_qrcodes/invoice_INV-C0A3749F_qr_h3AKA2K.png','card',2000.00,100.00,5.00,'Asia/Karachi'),(35,NULL,NULL,NULL,'8344db27-1758-4153-8839-b8d9e8612784','INV-0433DFCE',2301.00,'2026-06-21 02:27:16.122390',2,'931a78bcf2404e9384d3db272f91b810','invoice_qrcodes/invoice_INV-0433DFCE_qr_2GozFNb.png','cash',1950.00,351.00,18.00,'Asia/Karachi'),(36,NULL,NULL,NULL,'cb203166-fa93-4844-8fbb-a3558035c1cc','INV-8556D7A7',590.00,'2026-06-21 02:28:44.447576',2,'ec69cc077230487a8bbbfcd7ed68c540','invoice_qrcodes/invoice_INV-8556D7A7_qr_ngslzb4.png','cash',500.00,90.00,18.00,'Asia/Karachi'),(37,NULL,NULL,NULL,'5d9dc8b3-e262-4226-87b3-9eec1cf9a619','INV-EDF0E93B',36225.00,'2026-06-21 02:29:27.306451',2,'10d9bfb08e36464c9326150ff10a2142','invoice_qrcodes/invoice_INV-EDF0E93B_qr_q6vGo0o.png','card',34500.00,1725.00,5.00,'Asia/Karachi'),(38,NULL,NULL,NULL,'19692218-ca9a-4d06-b9d6-416ff520dd63','INV-E3CAF8A6',2572.50,'2026-06-21 02:41:29.629176',6,'b01582bb480d47729ce54a79a37b224a','invoice_qrcodes/invoice_INV-E3CAF8A6_qr_vMAz43Q.png','card',2450.00,122.50,5.00,'Asia/Karachi'),(39,NULL,NULL,NULL,'5b50e919-258a-4ecb-a290-aef2f060676d','INV-1A28086F',5670.00,'2026-06-21 02:42:39.525753',6,'b46f89d2c36542839ba39d1fc99224e9','invoice_qrcodes/invoice_INV-1A28086F_qr_Yyv1nAF.png','card',5400.00,270.00,5.00,'Asia/Karachi'),(40,NULL,NULL,NULL,'c10979b3-4abb-49c7-81a6-ec41abef56b0','INV-3593FDC2',1575.00,'2026-06-21 02:43:07.893966',6,'ae9afc1819c0441cbdb8716aca48b5b0','invoice_qrcodes/invoice_INV-3593FDC2_qr_EJAEL0z.png','card',1500.00,75.00,5.00,'Asia/Karachi'),(41,NULL,NULL,NULL,'ee1bc1c6-3636-4800-b0bc-b4f872db485f','INV-0AC0D389',2047.50,'2026-06-21 02:52:42.527572',6,'87663f8a2d2a486380f8b7d03c7bc0c3','invoice_qrcodes/invoice_INV-0AC0D389_qr_O0EGWbJ.png','card',1950.00,97.50,5.00,'Asia/Karachi'),(42,NULL,NULL,NULL,'96bddacf-4164-4aab-9a19-3be036799653','INV-8C4ED4A8',525.00,'2026-06-21 02:53:10.855699',6,'320bc3a6df634a81bebf7a47083444c1','invoice_qrcodes/invoice_INV-8C4ED4A8_qr_kUYqXzb.png','card',500.00,25.00,5.00,'Asia/Karachi'),(43,NULL,NULL,2,'c404570d-7d20-4b81-b561-13bc523d4917','INV-2F612DD3',3675.00,'2026-06-21 02:57:49.514007',NULL,'7ef819c84e7b48348b3bbb88ff8813e4','invoice_qrcodes/invoice_INV-2F612DD3_qr_phgcogM.png','card',3500.00,175.00,5.00,'Asia/Karachi'),(44,NULL,NULL,2,'e2c28937-4e86-41cc-aaac-1784c5fffa3e','INV-7313B195',1050.00,'2026-06-21 03:00:19.521353',NULL,'51cedd54fa944102ac284c83b987542a','invoice_qrcodes/invoice_INV-7313B195_qr_k1P37et.png','card',1000.00,50.00,5.00,'Asia/Karachi');
/*!40000 ALTER TABLE `users_invoice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_invoiceitem`
--

DROP TABLE IF EXISTS `users_invoiceitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_invoiceitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `product_name` varchar(255) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `quantity` int unsigned NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `invoice_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `users_invoiceitem_invoice_id_c5b7c162_fk_users_invoice_id` (`invoice_id`),
  CONSTRAINT `users_invoiceitem_invoice_id_c5b7c162_fk_users_invoice_id` FOREIGN KEY (`invoice_id`) REFERENCES `users_invoice` (`id`),
  CONSTRAINT `users_invoiceitem_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_invoiceitem`
--

LOCK TABLES `users_invoiceitem` WRITE;
/*!40000 ALTER TABLE `users_invoiceitem` DISABLE KEYS */;
INSERT INTO `users_invoiceitem` VALUES (1,'Burger',500.00,1,500.00,1),(2,'Apple Juice',1500.00,1,1500.00,1),(3,'Burger',500.00,1,500.00,2),(4,'Apple Juice',1500.00,1,1500.00,2),(5,'Fish',1950.00,1,1950.00,2),(6,'Fish',1950.00,2,3900.00,3),(7,'Burger',500.00,1,500.00,3),(8,'Apple Juice',1500.00,2,3000.00,4),(9,'Burger',500.00,5,2500.00,4),(10,'Fish',1950.00,1,1950.00,4),(11,'Burger',500.00,1,500.00,5),(12,'Apple Juice',1500.00,1,1500.00,5),(13,'Burger',500.00,5,2500.00,6),(14,'Apple Juice',1500.00,1,1500.00,6),(15,'Fish',1950.00,3,5850.00,6),(16,'Burger',500.00,2,1000.00,7),(17,'Apple Juice',1500.00,1,1500.00,7),(18,'Fish',1950.00,1,1950.00,7),(19,'Burger',500.00,2,1000.00,8),(20,'Apple Juice',1500.00,1,1500.00,8),(21,'Fish',1950.00,1,1950.00,8),(22,'Burger',500.00,2,1000.00,9),(23,'Apple Juice',1500.00,1,1500.00,9),(24,'Fish',1950.00,1,1950.00,9),(25,'Apple Juice',1500.00,1,1500.00,10),(26,'Fish',1950.00,1,1950.00,10),(27,'Apple Juice',1500.00,1,1500.00,11),(28,'Burger',500.00,2,1000.00,11),(29,'Burger',500.00,1,500.00,12),(30,'Apple Juice',1500.00,2,3000.00,12),(31,'Burger',500.00,1,500.00,13),(32,'Apple Juice',1500.00,1,1500.00,13),(33,'Burger',500.00,1,500.00,14),(34,'Apple Juice',1500.00,1,1500.00,14),(35,'Fish',1950.00,1,1950.00,14),(36,'Fish',1950.00,3,5850.00,15),(37,'Burger',500.00,1,500.00,16),(38,'Apple Juice',1500.00,1,1500.00,16),(39,'Burger',500.00,1,500.00,17),(40,'Apple Juice',1500.00,1,1500.00,17),(41,'Fish',1950.00,1,1950.00,18),(42,'Apple Juice',1500.00,1,1500.00,18),(43,'Burger',500.00,1,500.00,19),(44,'Apple Juice',1500.00,1,1500.00,19),(45,'Fish',1950.00,1,1950.00,20),(46,'Fish',1950.00,1,1950.00,21),(47,'Burger',500.00,1,500.00,22),(48,'Fish',1950.00,1,1950.00,23),(49,'Burger',500.00,1,500.00,24),(50,'Apple Juice',1500.00,2,3000.00,24),(51,'Fish',1950.00,1,1950.00,25),(52,'Burger',500.00,1,500.00,26),(53,'Apple Juice',1500.00,1,1500.00,27),(54,'Burger',500.00,1,500.00,28),(55,'Fish',1950.00,1,1950.00,29),(56,'Apple Juice',1500.00,1,1500.00,30),(57,'Burger',500.00,1,500.00,31),(58,'Burger',500.00,1,500.00,32),(59,'Apple Juice',1500.00,1,1500.00,32),(60,'Burger',500.00,1,500.00,33),(61,'Burger',500.00,1,500.00,34),(62,'Apple Juice',1500.00,1,1500.00,34),(63,'Fish',1950.00,1,1950.00,35),(64,'Burger',500.00,1,500.00,36),(65,'Apple Juice',1500.00,23,34500.00,37),(66,'Burger',500.00,1,500.00,38),(67,'Fish',1950.00,1,1950.00,38),(68,'Fish',1950.00,2,3900.00,39),(69,'Apple Juice',1500.00,1,1500.00,39),(70,'Apple Juice',1500.00,1,1500.00,40),(71,'Fish',1950.00,1,1950.00,41),(72,'Burger',500.00,1,500.00,42),(73,'Burger',500.00,1,500.00,43),(74,'Apple Juice',1500.00,2,3000.00,43),(75,'Burger',500.00,2,1000.00,44);
/*!40000 ALTER TABLE `users_invoiceitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_kitchenorder`
--

DROP TABLE IF EXISTS `users_kitchenorder`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_kitchenorder` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order_number` varchar(30) NOT NULL,
  `table_no` int DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `invoice_id` bigint NOT NULL,
  `uuid_token` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_number` (`order_number`),
  UNIQUE KEY `invoice_id` (`invoice_id`),
  UNIQUE KEY `users_kitchenorder_uuid_token_d23fbb7d_uniq` (`uuid_token`),
  CONSTRAINT `users_kitchenorder_invoice_id_e6c6b352_fk_users_invoice_id` FOREIGN KEY (`invoice_id`) REFERENCES `users_invoice` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_kitchenorder`
--

LOCK TABLES `users_kitchenorder` WRITE;
/*!40000 ALTER TABLE `users_kitchenorder` DISABLE KEYS */;
INSERT INTO `users_kitchenorder` VALUES (1,'ORD-1',NULL,'delivered','2026-06-19 18:24:46.159659',1,'5c74e26dda384c95ba6348f6342e1e2c'),(2,'ORD-2',3,'delivered','2026-06-19 18:36:41.311411',2,'90c8c825f49848709164d672824c2fe5'),(3,'ORD-3',NULL,'delivered','2026-06-19 23:10:30.034900',3,'825e356206fd4e2c9a1a88cc1ac7472c'),(4,'ORD-4',NULL,'delivered','2026-06-19 23:49:20.446462',4,'c7c5cbac3c0d4814845b8ec3893f7e74'),(5,'ORD-5',3,'delivered','2026-06-19 23:50:15.807991',5,'f68b53e5e0464f838c62ee5886a67fd1'),(6,'ORD-6',NULL,'delivered','2026-06-20 04:04:30.143428',6,'151cb1e651104133b4ae8681ae25b149'),(7,'ORD-7',NULL,'delivered','2026-06-20 05:29:09.892855',7,'b482f3a3f629469dac2bb72d4a4d4c66'),(8,'ORD-8',NULL,'delivered','2026-06-20 05:29:24.804138',8,'deddaa2d9c024c7daf3d8a60ee8583cf'),(9,'ORD-9',NULL,'delivered','2026-06-20 05:34:10.361266',9,'191c575c03234d98886b96328dc29b13'),(10,'ORD-10',NULL,'delivered','2026-06-20 05:39:42.560128',10,'a1a3e51f66124acf8b39aa20e28e3ded'),(11,'ORD-11',1,'delivered','2026-06-20 05:49:01.133794',11,'0020e421fbec42c0a6b379df5d700511'),(12,'ORD-12',NULL,'delivered','2026-06-21 01:59:31.350978',12,'d83e908876fd46c29321758502d2cf8f'),(13,'ORD-13',NULL,'delivered','2026-06-21 02:10:31.185112',13,'c99a0bed3aac49159c007d2d6216da3c'),(14,'ORD-14',NULL,'delivered','2026-06-21 02:57:42.906001',14,'9d92181046f643908d0c1128d18a5db6'),(15,'ORD-15',NULL,'delivered','2026-06-21 03:03:24.819104',15,'b8ce529d6a724b7ab04c2e6e1336b3ba'),(16,'ORD-16',NULL,'delivered','2026-06-21 03:15:48.160939',16,'3888f273fb254e019380dc53ff4c0223'),(17,'ORD-17',NULL,'delivered','2026-06-21 03:22:43.725450',17,'ffeb961f76994e039b5237f7d645ef84'),(18,'ORD-18',NULL,'delivered','2026-06-21 03:27:17.004935',18,'09b20608e6ab4f42a3823c2b27dc18cd'),(19,'ORD-19',NULL,'delivered','2026-06-21 03:30:42.220279',19,'dcb9f0ceceb741e2badc772aaca6dec1'),(20,'ORD-20',NULL,'delivered','2026-06-21 03:41:50.027253',20,'741a1db825f348ccac5d7ad3c194864f'),(21,'ORD-21',NULL,'delivered','2026-06-21 03:51:16.351252',21,'b30c89a38c024a6994f6716d61c77b22'),(22,'ORD-22',NULL,'delivered','2026-06-21 03:53:47.676931',22,'44e5d30ed2234a919d7c1d4d2d16d5af'),(23,'ORD-23',1,'delivered','2026-06-21 04:03:47.108786',23,'762546fa874a4296bb866eb87643b283'),(24,'ORD-24',NULL,'delivered','2026-06-21 04:57:28.217918',24,'b804e4cf3c8e41d3b8ef7b8c80ac9e24'),(25,'ORD-25',NULL,'delivered','2026-06-21 12:25:23.188783',25,'264d23928ccf4a889081eb892d2749ea'),(26,'ORD-26',NULL,'delivered','2026-06-21 12:26:45.342984',26,'a88d51848eb3441587e25ba8d6afd697'),(27,'ORD-27',NULL,'delivered','2026-06-21 13:29:15.882779',27,'4dbd120cae7a413da9399aeebb17a317'),(28,'ORD-28',NULL,'delivered','2026-06-21 02:01:15.676993',28,'41fcd13a24404b31aa76932a43e49134'),(29,'ORD-29',NULL,'delivered','2026-06-21 02:09:03.735384',29,'304e5ff6121743868b7ba650534ee757'),(30,'ORD-30',NULL,'delivered','2026-06-21 02:12:49.128686',30,'85de70dd36fa4c21b5bb94b1ca427856'),(31,'ORD-31',NULL,'delivered','2026-06-21 02:17:10.021672',31,'23566a784b5849a4a284a08fd7653793'),(32,'ORD-32',NULL,'delivered','2026-06-21 02:18:06.771806',32,'6abb03f64e104b01b2e97835db88ab7d'),(33,'ORD-33',NULL,'delivered','2026-06-21 02:18:55.224960',33,'3ab7a5c7342b41d5bf869573445fd7f5'),(34,'ORD-34',NULL,'delivered','2026-06-21 02:26:46.300521',34,'0f3a1a1084a34eea8d5fac8311e64ef6'),(35,'ORD-35',NULL,'delivered','2026-06-21 02:27:16.126915',35,'3487569051744bdd8d07733cd51a7ae0'),(36,'ORD-36',NULL,'delivered','2026-06-21 02:28:44.453249',36,'279545d5724642e5bdb8158440535e1a'),(37,'ORD-37',NULL,'delivered','2026-06-21 02:29:27.311302',37,'401bc5f402624357840c862df4162b55'),(38,'ORD-38',NULL,'delivered','2026-06-21 02:41:29.632668',38,'e9cdce4f94f84db9ba4e297fb0bcec84'),(39,'ORD-39',NULL,'delivered','2026-06-21 02:42:39.530111',39,'f262afd7f4ae44cd8da79b902c36d58b'),(40,'ORD-40',NULL,'delivered','2026-06-21 02:43:07.897612',40,'1dda64f9ae0942119787fbf6547e8169'),(41,'ORD-41',NULL,'delivered','2026-06-21 02:52:42.535391',41,'1b131596e77c4a98997cc84bbbc2123a'),(42,'ORD-42',NULL,'delivered','2026-06-21 02:53:10.859523',42,'8604b6d37c23453da32f707c44b6d2b8'),(43,'ORD-43',2,'delivered','2026-06-21 02:57:49.522722',43,'e6a52e972f1c43debae901011ecd6b7d'),(44,'ORD-44',2,'delivered','2026-06-21 03:00:19.525047',44,'63d6a7da0529468d8feea876bd194c40');
/*!40000 ALTER TABLE `users_kitchenorder` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_kitchenorderitem`
--

DROP TABLE IF EXISTS `users_kitchenorderitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_kitchenorderitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `product_name` varchar(255) NOT NULL,
  `quantity` int NOT NULL,
  `order_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `users_kitchenorderit_order_id_1194cca1_fk_users_kit` (`order_id`),
  CONSTRAINT `users_kitchenorderit_order_id_1194cca1_fk_users_kit` FOREIGN KEY (`order_id`) REFERENCES `users_kitchenorder` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_kitchenorderitem`
--

LOCK TABLES `users_kitchenorderitem` WRITE;
/*!40000 ALTER TABLE `users_kitchenorderitem` DISABLE KEYS */;
INSERT INTO `users_kitchenorderitem` VALUES (1,'Burger',1,1),(2,'Apple Juice',1,1),(3,'Burger',1,2),(4,'Apple Juice',1,2),(5,'Fish',1,2),(6,'Fish',2,3),(7,'Burger',1,3),(8,'Apple Juice',2,4),(9,'Burger',5,4),(10,'Fish',1,4),(11,'Burger',1,5),(12,'Apple Juice',1,5),(13,'Burger',5,6),(14,'Apple Juice',1,6),(15,'Fish',3,6),(16,'Burger',2,7),(17,'Apple Juice',1,7),(18,'Fish',1,7),(19,'Burger',2,8),(20,'Apple Juice',1,8),(21,'Fish',1,8),(22,'Burger',2,9),(23,'Apple Juice',1,9),(24,'Fish',1,9),(25,'Apple Juice',1,10),(26,'Fish',1,10),(27,'Apple Juice',1,11),(28,'Burger',2,11),(29,'Burger',1,12),(30,'Apple Juice',2,12),(31,'Burger',1,13),(32,'Apple Juice',1,13),(33,'Burger',1,14),(34,'Apple Juice',1,14),(35,'Fish',1,14),(36,'Fish',3,15),(37,'Burger',1,16),(38,'Apple Juice',1,16),(39,'Burger',1,17),(40,'Apple Juice',1,17),(41,'Fish',1,18),(42,'Apple Juice',1,18),(43,'Burger',1,19),(44,'Apple Juice',1,19),(45,'Fish',1,20),(46,'Fish',1,21),(47,'Burger',1,22),(48,'Fish',1,23),(49,'Burger',1,24),(50,'Apple Juice',2,24),(51,'Fish',1,25),(52,'Burger',1,26),(53,'Apple Juice',1,27),(54,'Burger',1,28),(55,'Fish',1,29),(56,'Apple Juice',1,30),(57,'Burger',1,31),(58,'Burger',1,32),(59,'Apple Juice',1,32),(60,'Burger',1,33),(61,'Burger',1,34),(62,'Apple Juice',1,34),(63,'Fish',1,35),(64,'Burger',1,36),(65,'Apple Juice',23,37),(66,'Burger',1,38),(67,'Fish',1,38),(68,'Fish',2,39),(69,'Apple Juice',1,39),(70,'Apple Juice',1,40),(71,'Fish',1,41),(72,'Burger',1,42),(73,'Burger',1,43),(74,'Apple Juice',2,43),(75,'Burger',2,44);
/*!40000 ALTER TABLE `users_kitchenorderitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_restauranttable`
--

DROP TABLE IF EXISTS `users_restauranttable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_restauranttable` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `table_no` int NOT NULL,
  `qr_code_image` varchar(100) DEFAULT NULL,
  `qr_token` varchar(64) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `table_no` (`table_no`),
  UNIQUE KEY `qr_token` (`qr_token`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_restauranttable`
--

LOCK TABLES `users_restauranttable` WRITE;
/*!40000 ALTER TABLE `users_restauranttable` DISABLE KEYS */;
INSERT INTO `users_restauranttable` VALUES (4,1,'table_qrcodes/table_1_qr.png','3CIh6MOJtmq32R3lxxKhXtCylwW3vrFf','2026-06-21 04:02:51.543616'),(5,2,'table_qrcodes/table_2_qr.png','QwNt3bRasHUylnKiJC5uzmfkSHBy6shV','2026-06-21 02:56:50.952590');
/*!40000 ALTER TABLE `users_restauranttable` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_user`
--

DROP TABLE IF EXISTS `users_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `email` varchar(254) NOT NULL,
  `name` varchar(255) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_operator` tinyint(1) NOT NULL,
  `is_kitchen` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `timezone` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_user`
--

LOCK TABLES `users_user` WRITE;
/*!40000 ALTER TABLE `users_user` DISABLE KEYS */;
INSERT INTO `users_user` VALUES (1,'argon2$argon2id$v=19$m=102400,t=2,p=8$MWY0bmdielBKMG1SR09YZjZncDVCeQ$f6iHv3SkVdbxYaCotBw4GCd991TMZr8q/ZentkT3sJI','2026-06-21 03:24:01.937227',1,'admin@123.com','',NULL,1,1,0,0,'2026-06-19 18:08:41.863196','Asia/Karachi'),(2,'argon2$argon2id$v=19$m=102400,t=2,p=8$cFhzcjEzNWh0N3hQdTRUZ0hPRXVwRw$bRBuYH6+i3IOIDtbzYLFn1Kv+Ar0Zr2e/ymSS/gohJs','2026-06-21 02:00:56.007431',0,'ali@123.com','Ali',NULL,1,0,0,0,'2026-06-19 18:24:10.697252','Asia/Karachi'),(3,'argon2$argon2id$v=19$m=102400,t=2,p=8$NHZ6ekl5M281ZDEzVnhjeGxHd2wwRQ$9t51MOCKLVDa4p82dPRHjdPNcWI89jMX+bkL7blcyiU','2026-06-21 02:58:27.094732',0,'salemm@123.com','salemm',NULL,1,0,0,1,'2026-06-19 18:25:57.323994','Asia/Karachi'),(5,'argon2$argon2id$v=19$m=102400,t=2,p=8$aVRvelJabmdsSWVWY2g0QjFvTTNJcQ$Sg6excjGP5cOAD7ZSwMujTKcxJeqxE0VHUl5XtXJDFA','2026-06-21 04:56:06.642000',0,'111@123.com','111',NULL,1,0,0,1,'2026-06-19 23:18:18.541025','Asia/Karachi'),(6,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z1k3TE9UeHZhTmNpajZoVHh5Y1N0cw$8zJXdelxOhYkAOHn1y1aGeCu4TZ5ZhKyzhOTmCthdjg','2026-06-21 02:40:51.563952',0,'khan@123.com','Khan',NULL,1,0,0,0,'2026-06-21 03:02:42.413581','Asia/Karachi');
/*!40000 ALTER TABLE `users_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_user_groups`
--

DROP TABLE IF EXISTS `users_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_user_groups_user_id_group_id_b88eab82_uniq` (`user_id`,`group_id`),
  KEY `users_user_groups_group_id_9afc8d0e_fk_auth_group_id` (`group_id`),
  CONSTRAINT `users_user_groups_group_id_9afc8d0e_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `users_user_groups_user_id_5f6f5a90_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_user_groups`
--

LOCK TABLES `users_user_groups` WRITE;
/*!40000 ALTER TABLE `users_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_user_user_permissions`
--

DROP TABLE IF EXISTS `users_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_user_user_permissions_user_id_permission_id_43338c45_uniq` (`user_id`,`permission_id`),
  KEY `users_user_user_perm_permission_id_0b93982e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `users_user_user_perm_permission_id_0b93982e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `users_user_user_permissions_user_id_20aca447_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_user_user_permissions`
--

LOCK TABLES `users_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `users_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-21  8:24:06
