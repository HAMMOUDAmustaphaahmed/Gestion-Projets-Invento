-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1
-- Généré le : ven. 16 jan. 2026 à 10:53
-- Version du serveur : 10.4.32-MariaDB
-- Version de PHP : 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `invento_db`
--

-- --------------------------------------------------------

--
-- Structure de la table `additional_cost`
--

CREATE TABLE `additional_cost` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `justification` text DEFAULT NULL,
  `date` date DEFAULT curdate(),
  `created_at` datetime DEFAULT current_timestamp(),
  `task_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `additional_cost`
--

INSERT INTO `additional_cost` (`id`, `name`, `amount`, `justification`, `date`, `created_at`, `task_id`) VALUES
(1, 'test', 100.00, 'zeraefzef', '2026-01-13', '2026-01-13 08:16:12', 1);

-- --------------------------------------------------------

--
-- Structure de la table `client`
--

CREATE TABLE `client` (
  `id` int(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `company` varchar(128) DEFAULT NULL,
  `contact_person` varchar(128) DEFAULT NULL,
  `email` varchar(128) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `city` varchar(64) DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  `country` varchar(64) DEFAULT NULL,
  `website` varchar(128) DEFAULT NULL,
  `siret` varchar(64) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `client`
--

INSERT INTO `client` (`id`, `name`, `company`, `contact_person`, `email`, `phone`, `address`, `city`, `postal_code`, `country`, `website`, `siret`, `notes`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'Client par défaut', 'À définir', 'Foulan Flani', 'foulan.flani@gmail.com', '12345678', 'aefzefssdc', 'fzefzef', '0000', 'Tunisie', 'client.com', NULL, 'Client créé pour le test', 1, '2026-01-13 10:53:12', '2026-01-13 10:01:24');

-- --------------------------------------------------------

--
-- Structure de la table `dashboard_chart`
--

CREATE TABLE `dashboard_chart` (
  `id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `chart_type` varchar(32) NOT NULL,
  `data_source` varchar(64) NOT NULL,
  `config` text DEFAULT NULL,
  `position` int(11) DEFAULT 0,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `user_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `dashboard_chart`
--

INSERT INTO `dashboard_chart` (`id`, `title`, `chart_type`, `data_source`, `config`, `position`, `is_active`, `created_at`, `user_id`) VALUES
(1, 'test', 'doughnut', 'stock', '{\"type\": \"line\", \"data\": {\"labels\": [], \"datasets\": [{\"label\": \"\", \"data\": [], \"backgroundColor\": [], \"borderColor\": [], \"borderWidth\": 1}]}, \"options\": {\"responsive\": true, \"maintainAspectRatio\": false, \"plugins\": {\"legend\": {\"position\": \"top\"}, \"title\": {\"display\": true, \"text\": \"\"}}, \"title\": {\"display\": true, \"text\": \"test\"}}}', 1, 1, '2026-01-12 11:17:29', 1),
(3, 'test1', 'doughnut', 'personnel', '{\"width\": \"6\", \"height\": \"300\"}', 2, 1, '2026-01-12 11:31:10', 1),
(4, 'abc', 'radar', 'projects', '{\"width\": \"6\", \"height\": \"300\"}', 3, 1, '2026-01-12 11:32:00', 1),
(5, 'azefaef', 'pie', 'stock_by_category', '{\"width\": \"6\", \"height\": \"300\"}', 4, 1, '2026-01-12 11:32:27', 1),
(6, 'taches', 'line', 'tasks', '{\"width\": \"6\", \"height\": \"300\"}', 5, 1, '2026-01-13 11:21:09', 1);

-- --------------------------------------------------------

--
-- Structure de la table `group`
--

CREATE TABLE `group` (
  `id` int(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `group`
--

INSERT INTO `group` (`id`, `name`, `description`, `created_at`) VALUES
(1, 'Équipe Maintenance', 'Équipe responsable de la maintenance préventive et corrective', '2026-01-11 13:13:47'),
(2, 'Équipe Stock', 'Équipe de gestion des stocks', '2026-01-11 13:13:47'),
(3, 'test', 'sdvsdv', '2026-01-11 17:36:20');

-- --------------------------------------------------------

--
-- Structure de la table `group_members`
--

CREATE TABLE `group_members` (
  `group_id` int(11) NOT NULL,
  `personnel_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `group_members`
--

INSERT INTO `group_members` (`group_id`, `personnel_id`) VALUES
(1, 1),
(1, 3),
(2, 2);

-- --------------------------------------------------------

--
-- Structure de la table `intervention`
--

CREATE TABLE `intervention` (
  `id` int(11) NOT NULL,
  `intervention_number` varchar(50) NOT NULL,
  `client_name` varchar(200) NOT NULL,
  `location` varchar(200) DEFAULT NULL,
  `type_id` int(11) DEFAULT NULL,
  `class_id` int(11) DEFAULT NULL,
  `entity_id` int(11) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `client_contact_date` date NOT NULL,
  `intervention_date` date NOT NULL,
  `planned_end_date` date NOT NULL,
  `actual_end_date` date DEFAULT NULL,
  `status` enum('planned','in_progress','completed','cancelled') NOT NULL DEFAULT 'planned',
  `anomaly_description` text DEFAULT NULL,
  `tasks_description` text DEFAULT NULL,
  `linked_to_project` tinyint(1) DEFAULT 0,
  `justification_delay` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `intervention`
--

INSERT INTO `intervention` (`id`, `intervention_number`, `client_name`, `location`, `type_id`, `class_id`, `entity_id`, `project_id`, `client_contact_date`, `intervention_date`, `planned_end_date`, `actual_end_date`, `status`, `anomaly_description`, `tasks_description`, `linked_to_project`, `justification_delay`, `created_at`, `updated_at`, `created_by`, `updated_by`) VALUES
(1, 'OM2026-001', 'client001', 'Sousse', 5, 3, 2, NULL, '2026-01-15', '2026-01-15', '2026-01-17', NULL, 'in_progress', 'azdfazfazf', 'azfazfazf', 0, '', '2026-01-15 13:37:50', '2026-01-15 13:37:50', 1, NULL);

-- --------------------------------------------------------

--
-- Structure de la table `intervention_class`
--

CREATE TABLE `intervention_class` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `created_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `intervention_class`
--

INSERT INTO `intervention_class` (`id`, `name`, `description`, `created_at`, `updated_at`, `created_by`) VALUES
(3, 'C.C', 'Curative', '2026-01-15 12:45:50', '2026-01-15 13:04:34', NULL),
(4, 'P.R', 'Intervention preventive', '2026-01-15 12:45:50', '2026-01-15 13:04:24', NULL);

-- --------------------------------------------------------

--
-- Structure de la table `intervention_cost`
--

CREATE TABLE `intervention_cost` (
  `id` int(11) NOT NULL,
  `intervention_id` int(11) NOT NULL,
  `cost_name` varchar(100) NOT NULL,
  `amount` decimal(10,2) NOT NULL DEFAULT 0.00,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `intervention_entity`
--

CREATE TABLE `intervention_entity` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `created_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `intervention_entity`
--

INSERT INTO `intervention_entity` (`id`, `name`, `description`, `created_at`, `updated_at`, `created_by`) VALUES
(1, 'TPX', 'Tunisie Panneaux', '2026-01-15 12:45:50', '2026-01-15 14:05:49', NULL),
(2, 'GPM', 'Cogepam', '2026-01-15 12:45:50', '2026-01-15 14:06:01', NULL);

-- --------------------------------------------------------

--
-- Structure de la table `intervention_personnel`
--

CREATE TABLE `intervention_personnel` (
  `intervention_id` int(11) NOT NULL,
  `personnel_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `intervention_personnel`
--

INSERT INTO `intervention_personnel` (`intervention_id`, `personnel_id`) VALUES
(1, 1);

-- --------------------------------------------------------

--
-- Structure de la table `intervention_stock`
--

CREATE TABLE `intervention_stock` (
  `id` int(11) NOT NULL,
  `intervention_id` int(11) NOT NULL,
  `stock_item_id` int(11) NOT NULL,
  `estimated_quantity` decimal(10,2) DEFAULT 0.00,
  `actual_quantity` decimal(10,2) DEFAULT NULL,
  `remaining_quantity` decimal(10,2) DEFAULT 0.00,
  `additional_quantity` decimal(10,2) DEFAULT 0.00,
  `justification` text DEFAULT NULL,
  `validated` tinyint(1) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `intervention_type`
--

CREATE TABLE `intervention_type` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `created_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `intervention_type`
--

INSERT INTO `intervention_type` (`id`, `name`, `description`, `created_at`, `updated_at`, `created_by`) VALUES
(2, 'EM', 'Intervention électromécanique ', '2026-01-15 12:45:50', '2026-01-15 13:02:57', NULL),
(3, 'FR', 'Froid', '2026-01-15 12:45:50', '2026-01-15 13:02:17', NULL),
(4, 'MC', 'Intervention mécanique ', '2026-01-15 12:45:50', '2026-01-15 13:01:50', NULL),
(5, 'EC', 'Intervention électrique ', '2026-01-15 12:45:50', '2026-01-15 13:00:56', NULL);

-- --------------------------------------------------------

--
-- Structure de la table `notification`
--

CREATE TABLE `notification` (
  `id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `notification_type` varchar(32) DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  `user_id` int(11) NOT NULL,
  `stock_item_id` int(11) DEFAULT NULL,
  `task_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `personnel`
--

CREATE TABLE `personnel` (
  `id` int(11) NOT NULL,
  `employee_id` varchar(64) NOT NULL,
  `first_name` varchar(64) NOT NULL,
  `last_name` varchar(64) NOT NULL,
  `email` varchar(120) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `department` varchar(64) DEFAULT NULL,
  `position` varchar(64) DEFAULT NULL,
  `hire_date` date DEFAULT NULL,
  `address` text DEFAULT NULL,
  `city` varchar(64) DEFAULT NULL,
  `country` varchar(64) DEFAULT NULL,
  `emergency_contact` varchar(128) DEFAULT NULL,
  `emergency_phone` varchar(20) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `personnel`
--

INSERT INTO `personnel` (`id`, `employee_id`, `first_name`, `last_name`, `email`, `phone`, `department`, `position`, `hire_date`, `address`, `city`, `country`, `emergency_contact`, `emergency_phone`, `notes`, `is_active`, `created_at`) VALUES
(1, 'EMP001', 'Mohamed', 'Ahmed', 'm.ahmed@invento.com', '+33 6 12 34 56 78', 'Maintenance', 'Technicien Senior', '2020-01-15', NULL, 'Paris', 'France', NULL, NULL, NULL, 1, '2026-01-11 13:13:47'),
(2, 'EMP002', 'Sophie', 'Leclerc', 's.leclerc@invento. com', '+33 6 23 45 67 89', 'Gestion de Stock', 'Responsable Stock', '2019-06-01', NULL, 'Paris', 'France', NULL, NULL, NULL, 1, '2026-01-11 13:13:47'),
(3, 'EMP003', 'Pierre', 'Moreau', 'p.moreau@invento.com', '+33 6 34 56 78 90', 'Maintenance', 'Technicien', '2021-03-10', NULL, 'Lyon', 'France', NULL, NULL, NULL, 1, '2026-01-11 13:13:47');

-- --------------------------------------------------------

--
-- Structure de la table `project`
--

CREATE TABLE `project` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `actual_end_date` date DEFAULT NULL,
  `estimated_budget` decimal(12,2) DEFAULT 0.00,
  `actual_cost` decimal(12,2) DEFAULT 0.00,
  `status` varchar(32) DEFAULT 'planning',
  `priority` varchar(32) DEFAULT 'medium',
  `notes` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `client_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `project`
--

INSERT INTO `project` (`id`, `name`, `description`, `start_date`, `end_date`, `actual_end_date`, `estimated_budget`, `actual_cost`, `status`, `priority`, `notes`, `created_at`, `updated_at`, `client_id`) VALUES
(1, 'test', 'qfqfqfq', '2026-01-12', '2026-01-15', NULL, 15000.00, 0.00, 'planning', 'medium', 'qfqf', '2026-01-12 11:39:18', '2026-01-13 10:53:26', 1);

-- --------------------------------------------------------

--
-- Structure de la table `project_file`
--

CREATE TABLE `project_file` (
  `id` int(11) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `file_type` varchar(10) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `uploaded_at` datetime DEFAULT current_timestamp(),
  `project_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `project_file`
--

INSERT INTO `project_file` (`id`, `filename`, `original_filename`, `file_type`, `description`, `uploaded_at`, `project_id`) VALUES
(2, 'a6bb5f3e4b074a69bd48f4e8ea65a9a4.jpg', 'logo.jpg', 'jpg', 'logo', '2026-01-13 08:04:14', 1);

-- --------------------------------------------------------

--
-- Structure de la table `role`
--

CREATE TABLE `role` (
  `id` int(11) NOT NULL,
  `name` varchar(64) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `permissions` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `role`
--

INSERT INTO `role` (`id`, `name`, `description`, `permissions`) VALUES
(1, 'admin', 'Administrateur système avec tous les droits', '{\"admin\": {\"all\": true}, \"stock\": {\"read\": true, \"create\": true, \"update\": true, \"delete\": true, \"export\": true}, \"projects\": {\"read\": true, \"create\": true, \"update\": true, \"delete\": true, \"export\": true}, \"tasks\": {\"read\": true, \"create\": true, \"update\": true, \"delete\": true, \"export\": true}, \"personnel\": {\"read\": true, \"create\": true, \"update\": true, \"delete\": true, \"export\": true}, \"calendar\": {\"read\": true, \"create\": true, \"update\": true, \"export\": true}, \"dashboard\": {\"read\": true, \"create\": true, \"update\": true, \"export\": true}, \"settings\": {\"all\": true}}'),
(2, 'gestionnaire', 'Gestionnaire avec droits étendus', '{\"stock\": {\"read\": true, \"create\": true, \"update\": true, \"delete\": false, \"export\": true}, \"projects\": {\"read\": true, \"create\": true, \"update\": true, \"delete\": false, \"export\": true}, \"tasks\": {\"read\": true, \"create\": true, \"update\": true, \"delete\": false, \"export\": true}, \"personnel\": {\"read\": true, \"create\": true, \"update\": true, \"delete\": false}, \"calendar\": {\"read\": true, \"create\": true, \"update\": true}, \"dashboard\": {\"read\": true, \"create\": true, \"update\": true, \"export\": true}}'),
(3, 'technicien', 'Technicien avec droits limités', '{\"stock\": {\"read\": true, \"create\": false, \"update\": false, \"delete\": false}, \"projects\": {\"read\": true, \"create\": false, \"update\": false, \"delete\": false}, \"tasks\": {\"read\": true, \"create\": false, \"update\": true, \"delete\": false}, \"personnel\": {\"read\": false, \"create\": false, \"update\": false, \"delete\": false}, \"calendar\": {\"read\": true, \"create\": false, \"update\": false}, \"dashboard\": {\"read\": true, \"create\": false, \"update\": false}}'),
(4, 'consultant', 'Consultant en lecture seule', '{\"stock\": {\"read\": true, \"create\": false, \"update\": false, \"delete\": false}, \"projects\": {\"read\": true, \"create\": false, \"update\": false, \"delete\": false}, \"tasks\": {\"read\": true, \"create\": false, \"update\": false, \"delete\": false}, \"personnel\": {\"read\": false, \"create\": false, \"update\": false, \"delete\": false}, \"calendar\": {\"read\": true, \"create\": false, \"update\": false}, \"dashboard\": {\"read\": true, \"create\": false, \"update\": false}}');

-- --------------------------------------------------------

--
-- Structure de la table `stock_attribute`
--

CREATE TABLE `stock_attribute` (
  `id` int(11) NOT NULL,
  `name` varchar(64) NOT NULL,
  `value` varchar(255) DEFAULT NULL,
  `data_type` varchar(32) DEFAULT 'string',
  `stock_item_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `stock_category`
--

CREATE TABLE `stock_category` (
  `id` int(11) NOT NULL,
  `name` varchar(64) NOT NULL,
  `description` text DEFAULT NULL,
  `attributes_template` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `stock_category`
--

INSERT INTO `stock_category` (`id`, `name`, `description`, `attributes_template`, `created_at`) VALUES
(1, 'Pièces détachées', 'Pièces de rechange pour équipements', NULL, '2026-01-12 14:28:13'),
(2, 'Outillage', 'Outils manuels et électriques', NULL, '2026-01-12 14:28:13'),
(3, 'Consommables', 'Matériaux consommables', NULL, '2026-01-12 14:28:13'),
(4, 'Équipement de sécurité', 'Équipements de protection individuelle', NULL, '2026-01-12 14:28:13'),
(5, 'Matériel informatique', 'Ordinateurs, périphériques et composants', NULL, '2026-01-12 14:28:13'),
(6, 'test', 'sdvsdv', NULL, '2026-01-12 14:28:13');

-- --------------------------------------------------------

--
-- Structure de la table `stock_file`
--

CREATE TABLE `stock_file` (
  `id` int(11) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `file_type` varchar(10) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `uploaded_at` datetime DEFAULT current_timestamp(),
  `stock_item_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Structure de la table `stock_item`
--

CREATE TABLE `stock_item` (
  `id` int(11) NOT NULL,
  `reference` varchar(64) NOT NULL,
  `libelle` varchar(255) NOT NULL,
  `item_type` varchar(64) NOT NULL,
  `quantity` decimal(10,2) DEFAULT 0.00,
  `min_quantity` decimal(10,2) DEFAULT 0.00,
  `price` decimal(10,2) DEFAULT 0.00,
  `value` decimal(12,2) DEFAULT 0.00,
  `location` varchar(128) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `supplier_id` int(11) DEFAULT NULL,
  `category_id` int(11) DEFAULT NULL,
  `unit` varchar(32) DEFAULT 'piece'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `stock_item`
--

INSERT INTO `stock_item` (`id`, `reference`, `libelle`, `item_type`, `quantity`, `min_quantity`, `price`, `value`, `location`, `notes`, `created_at`, `updated_at`, `supplier_id`, `category_id`, `unit`) VALUES
(1, 'PRT-001', 'Porte', '1', 100.00, 20.00, 10.00, 1000.00, 'R1-E3', 'zefzef', '2026-01-11 17:13:32', '2026-01-11 17:13:32', 1, 1, 'piece'),
(2, 'EVP-001', 'Evap', '2', 120.00, 20.00, 1000.00, 120000.00, 'E2R5', 'zevqvsqdv', '2026-01-15 14:31:20', '2026-01-15 14:31:20', 2, 2, 'piece');

-- --------------------------------------------------------

--
-- Structure de la table `supplier`
--

CREATE TABLE `supplier` (
  `id` int(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `contact_person` varchar(128) DEFAULT NULL,
  `email` varchar(128) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `city` varchar(64) DEFAULT NULL,
  `country` varchar(64) DEFAULT NULL,
  `website` varchar(128) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `supplier`
--

INSERT INTO `supplier` (`id`, `name`, `contact_person`, `email`, `phone`, `address`, `city`, `country`, `website`, `notes`, `created_at`) VALUES
(1, 'Fournitures Industrielles SA', 'Jean Dupont', 'contact@fournitures-ind.com', '+33 1 23 45 67 89', NULL, 'Paris', 'France', 'www.fournitures-ind.com', NULL, '2026-01-11 13:13:47'),
(2, 'ElectroTech Solutions', 'Marie Martin', 'ventes@electrotech.fr', '+33 2 34 56 78 90', NULL, 'Lyon', 'France', 'www.electrotech.fr', NULL, '2026-01-11 13:13:47'),
(3, 'test', '1234', 'test@gmail.com', '1234', 'sdvsdv', 'vsdvsdv', 'sdvsdv', 'ssdvsdvsdv', 'sdvsdvsd', '2026-01-11 17:16:16');

-- --------------------------------------------------------

--
-- Structure de la table `task`
--

CREATE TABLE `task` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `actual_end_date` date DEFAULT NULL,
  `status` varchar(32) DEFAULT 'pending',
  `priority` varchar(32) DEFAULT 'medium',
  `use_stock` tinyint(1) DEFAULT 1,
  `justification` text DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `project_id` int(11) NOT NULL,
  `task_type_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `task`
--

INSERT INTO `task` (`id`, `name`, `description`, `start_date`, `end_date`, `actual_end_date`, `status`, `priority`, `use_stock`, `justification`, `notes`, `created_at`, `updated_at`, `project_id`, `task_type_id`) VALUES
(1, 'test', 'svsdsd', '2026-01-12', '2026-01-15', '2026-01-13', 'completed', 'medium', 0, 'zsegze\n\n[TERMINÉ AVEC ERREUR - 13/01/2026 12:20]: zeafnlozn', 'gezg\n\nTemps supplémentaire nécessaire: 1 jour', '2026-01-12 13:21:28', '2026-01-13 11:20:06', 1, 3),
(3, 'test1', 'ghjkm', '2026-01-13', '2026-01-17', '2026-01-13', 'completed', 'high', 1, NULL, NULL, '2026-01-12 15:19:27', '2026-01-13 11:20:41', 1, 3),
(7, 'test11', 'ababab', '2026-01-13', '2026-01-17', NULL, 'in_progress', 'high', 0, NULL, NULL, '2026-01-13 10:54:37', '2026-01-13 11:04:44', 1, 3);

-- --------------------------------------------------------

--
-- Structure de la table `task_groups`
--

CREATE TABLE `task_groups` (
  `task_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `task_groups`
--

INSERT INTO `task_groups` (`task_id`, `group_id`) VALUES
(3, 1);

-- --------------------------------------------------------

--
-- Structure de la table `task_personnel`
--

CREATE TABLE `task_personnel` (
  `task_id` int(11) NOT NULL,
  `personnel_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `task_personnel`
--

INSERT INTO `task_personnel` (`task_id`, `personnel_id`) VALUES
(1, 3),
(3, 1),
(3, 2),
(4, 1),
(4, 2),
(5, 3),
(6, 1),
(6, 2),
(7, 1),
(7, 2);

-- --------------------------------------------------------

--
-- Structure de la table `task_stock_item`
--

CREATE TABLE `task_stock_item` (
  `id` int(11) NOT NULL,
  `estimated_quantity` decimal(10,2) DEFAULT 0.00,
  `actual_quantity_used` decimal(10,2) DEFAULT NULL,
  `remaining_quantity` decimal(10,2) DEFAULT NULL,
  `estimated_cost` decimal(10,2) DEFAULT NULL,
  `return_to_stock` tinyint(1) DEFAULT 0,
  `notes` text DEFAULT NULL,
  `task_id` int(11) NOT NULL,
  `stock_item_id` int(11) DEFAULT NULL,
  `unit` varchar(32) DEFAULT 'piece',
  `justification_shortage` text DEFAULT NULL,
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `created_at` datetime DEFAULT current_timestamp(),
  `additional_quantity` decimal(10,2) DEFAULT 0.00,
  `unit_type` varchar(32) DEFAULT 'piece'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `task_stock_item`
--

INSERT INTO `task_stock_item` (`id`, `estimated_quantity`, `actual_quantity_used`, `remaining_quantity`, `estimated_cost`, `return_to_stock`, `notes`, `task_id`, `stock_item_id`, `unit`, `justification_shortage`, `updated_at`, `created_at`, `additional_quantity`, `unit_type`) VALUES
(2, 90.00, NULL, NULL, NULL, 0, 'sdvsd', 1, 1, 'piece', NULL, '2026-01-12 15:10:46', '2026-01-12 15:10:46', 0.00, 'piece'),
(3, 3.00, NULL, NULL, NULL, 1, '', 1, 1, 'piece', NULL, '2026-01-12 15:15:43', '2026-01-12 15:15:43', 0.00, 'piece');

-- --------------------------------------------------------

--
-- Structure de la table `task_type`
--

CREATE TABLE `task_type` (
  `id` int(11) NOT NULL,
  `name` varchar(64) NOT NULL,
  `description` text DEFAULT NULL,
  `default_duration` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `task_type`
--

INSERT INTO `task_type` (`id`, `name`, `description`, `default_duration`, `created_at`) VALUES
(1, 'Contrat Maintenance préventive', 'Maintenance planifiée', 2, '2026-01-11 13:13:47'),
(2, 'Maintenance corrective', 'Réparation suite à panne', 4, '2026-01-11 13:13:47'),
(3, 'Installation', 'Installation d\'équipement', 8, '2026-01-11 13:13:47'),
(4, 'Inspection', 'Contrôle et vérification', 1, '2026-01-11 13:13:47'),
(5, 'Calibration', 'Étalonnage d\'équipement', 3, '2026-01-11 13:13:47'),
(6, 'test', 'sdfvsdv', 5, '2026-01-11 17:24:06');

-- --------------------------------------------------------

--
-- Structure de la table `user`
--

CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `username` varchar(64) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(256) NOT NULL,
  `first_name` varchar(64) DEFAULT NULL,
  `last_name` varchar(64) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `last_login` datetime DEFAULT NULL,
  `role_id` int(11) DEFAULT NULL,
  `last_seen` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `user`
--

INSERT INTO `user` (`id`, `username`, `email`, `password_hash`, `first_name`, `last_name`, `is_active`, `created_at`, `last_login`, `role_id`, `last_seen`) VALUES
(1, 'admin', 'admin@gmao.com', 'scrypt:32768:8:1$u3bwTWrmLGYfhGcd$6366c4d4c70daf8db8a23a0c2d712be101b55beb4f597fcba6ed1455f481e750c795faf1088f1fa1b70498911b55efed82608aca5392e70628d7406ef362a338', 'Administrateur', 'Système', 1, '2026-01-11 13:13:47', '2026-01-16 09:29:29', 1, '2026-01-14 12:55:59'),
(2, 'user', 'user@gmail.com', 'scrypt:32768:8:1$saS4xWd2fSPTrL8F$9f60986026aa7c1074cc65eabf7013250db3252d49390cc9caaed8a21a2586998102068d0a5322ca882c9ffd42c4619349082032f3d5f0a24702b30fab03492b', 'flen', 'foulani', 1, '2026-01-12 14:39:42', NULL, 4, NULL);

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `additional_cost`
--
ALTER TABLE `additional_cost`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_additional_cost_task` (`task_id`);

--
-- Index pour la table `client`
--
ALTER TABLE `client`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `dashboard_chart`
--
ALTER TABLE `dashboard_chart`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_chart_user` (`user_id`),
  ADD KEY `idx_chart_active` (`is_active`);

--
-- Index pour la table `group`
--
ALTER TABLE `group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `idx_group_name` (`name`);

--
-- Index pour la table `group_members`
--
ALTER TABLE `group_members`
  ADD PRIMARY KEY (`group_id`,`personnel_id`),
  ADD KEY `personnel_id` (`personnel_id`);

--
-- Index pour la table `intervention`
--
ALTER TABLE `intervention`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `intervention_number` (`intervention_number`),
  ADD KEY `type_id` (`type_id`),
  ADD KEY `class_id` (`class_id`),
  ADD KEY `entity_id` (`entity_id`),
  ADD KEY `project_id` (`project_id`),
  ADD KEY `created_by` (`created_by`),
  ADD KEY `updated_by` (`updated_by`),
  ADD KEY `idx_intervention_number` (`intervention_number`),
  ADD KEY `idx_client_name` (`client_name`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_intervention_date` (`intervention_date`);

--
-- Index pour la table `intervention_class`
--
ALTER TABLE `intervention_class`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `created_by` (`created_by`);

--
-- Index pour la table `intervention_cost`
--
ALTER TABLE `intervention_cost`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_intervention_cost` (`intervention_id`);

--
-- Index pour la table `intervention_entity`
--
ALTER TABLE `intervention_entity`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `created_by` (`created_by`);

--
-- Index pour la table `intervention_personnel`
--
ALTER TABLE `intervention_personnel`
  ADD PRIMARY KEY (`intervention_id`,`personnel_id`),
  ADD KEY `personnel_id` (`personnel_id`),
  ADD KEY `idx_intervention_personnel` (`intervention_id`,`personnel_id`);

--
-- Index pour la table `intervention_stock`
--
ALTER TABLE `intervention_stock`
  ADD PRIMARY KEY (`id`),
  ADD KEY `stock_item_id` (`stock_item_id`),
  ADD KEY `idx_intervention_stock` (`intervention_id`,`stock_item_id`);

--
-- Index pour la table `intervention_type`
--
ALTER TABLE `intervention_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `created_by` (`created_by`);

--
-- Index pour la table `notification`
--
ALTER TABLE `notification`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_notification_user` (`user_id`,`is_read`),
  ADD KEY `idx_notification_created` (`created_at`),
  ADD KEY `stock_item_id` (`stock_item_id`),
  ADD KEY `task_id` (`task_id`);

--
-- Index pour la table `personnel`
--
ALTER TABLE `personnel`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `employee_id` (`employee_id`),
  ADD KEY `idx_personnel_employee_id` (`employee_id`),
  ADD KEY `idx_personnel_name` (`last_name`,`first_name`);

--
-- Index pour la table `project`
--
ALTER TABLE `project`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_project_status` (`status`),
  ADD KEY `idx_project_priority` (`priority`),
  ADD KEY `idx_project_dates` (`start_date`,`end_date`),
  ADD KEY `idx_project_status_date` (`status`,`start_date`),
  ADD KEY `fk_project_client` (`client_id`);

--
-- Index pour la table `project_file`
--
ALTER TABLE `project_file`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_file_project` (`project_id`);

--
-- Index pour la table `role`
--
ALTER TABLE `role`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `idx_role_name` (`name`);

--
-- Index pour la table `stock_attribute`
--
ALTER TABLE `stock_attribute`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_attribute_name` (`name`),
  ADD KEY `stock_item_id` (`stock_item_id`);

--
-- Index pour la table `stock_category`
--
ALTER TABLE `stock_category`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `idx_category_name` (`name`);

--
-- Index pour la table `stock_file`
--
ALTER TABLE `stock_file`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_file_stock_item` (`stock_item_id`);

--
-- Index pour la table `stock_item`
--
ALTER TABLE `stock_item`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `reference` (`reference`),
  ADD KEY `idx_stock_reference` (`reference`),
  ADD KEY `idx_stock_item_type` (`item_type`),
  ADD KEY `idx_stock_quantity` (`quantity`),
  ADD KEY `supplier_id` (`supplier_id`),
  ADD KEY `category_id` (`category_id`),
  ADD KEY `idx_stock_item_category` (`category_id`);

--
-- Index pour la table `supplier`
--
ALTER TABLE `supplier`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_supplier_name` (`name`);

--
-- Index pour la table `task`
--
ALTER TABLE `task`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_task_status` (`status`),
  ADD KEY `idx_task_priority` (`priority`),
  ADD KEY `idx_task_dates` (`start_date`,`end_date`),
  ADD KEY `idx_task_project` (`project_id`),
  ADD KEY `task_type_id` (`task_type_id`),
  ADD KEY `idx_task_status_date` (`status`,`start_date`);

--
-- Index pour la table `task_groups`
--
ALTER TABLE `task_groups`
  ADD PRIMARY KEY (`task_id`,`group_id`),
  ADD KEY `group_id` (`group_id`);

--
-- Index pour la table `task_personnel`
--
ALTER TABLE `task_personnel`
  ADD PRIMARY KEY (`task_id`,`personnel_id`),
  ADD KEY `personnel_id` (`personnel_id`);

--
-- Index pour la table `task_stock_item`
--
ALTER TABLE `task_stock_item`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_task_stock_task` (`task_id`),
  ADD KEY `idx_task_stock_item` (`stock_item_id`);

--
-- Index pour la table `task_type`
--
ALTER TABLE `task_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `idx_task_type_name` (`name`);

--
-- Index pour la table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_user_username` (`username`),
  ADD KEY `idx_user_email` (`email`),
  ADD KEY `role_id` (`role_id`),
  ADD KEY `idx_user_role` (`role_id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `additional_cost`
--
ALTER TABLE `additional_cost`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `client`
--
ALTER TABLE `client`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `dashboard_chart`
--
ALTER TABLE `dashboard_chart`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT pour la table `group`
--
ALTER TABLE `group`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT pour la table `intervention`
--
ALTER TABLE `intervention`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `intervention_class`
--
ALTER TABLE `intervention_class`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT pour la table `intervention_cost`
--
ALTER TABLE `intervention_cost`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `intervention_entity`
--
ALTER TABLE `intervention_entity`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT pour la table `intervention_stock`
--
ALTER TABLE `intervention_stock`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `intervention_type`
--
ALTER TABLE `intervention_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT pour la table `notification`
--
ALTER TABLE `notification`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `personnel`
--
ALTER TABLE `personnel`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT pour la table `project`
--
ALTER TABLE `project`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `project_file`
--
ALTER TABLE `project_file`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `role`
--
ALTER TABLE `role`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT pour la table `stock_attribute`
--
ALTER TABLE `stock_attribute`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `stock_category`
--
ALTER TABLE `stock_category`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT pour la table `stock_file`
--
ALTER TABLE `stock_file`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `stock_item`
--
ALTER TABLE `stock_item`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `supplier`
--
ALTER TABLE `supplier`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT pour la table `task`
--
ALTER TABLE `task`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT pour la table `task_stock_item`
--
ALTER TABLE `task_stock_item`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT pour la table `task_type`
--
ALTER TABLE `task_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT pour la table `user`
--
ALTER TABLE `user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `additional_cost`
--
ALTER TABLE `additional_cost`
  ADD CONSTRAINT `additional_cost_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `dashboard_chart`
--
ALTER TABLE `dashboard_chart`
  ADD CONSTRAINT `dashboard_chart_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `group_members`
--
ALTER TABLE `group_members`
  ADD CONSTRAINT `group_members_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `group` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `group_members_ibfk_2` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `intervention`
--
ALTER TABLE `intervention`
  ADD CONSTRAINT `intervention_ibfk_1` FOREIGN KEY (`type_id`) REFERENCES `intervention_type` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `intervention_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `intervention_class` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `intervention_ibfk_3` FOREIGN KEY (`entity_id`) REFERENCES `intervention_entity` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `intervention_ibfk_4` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `intervention_ibfk_5` FOREIGN KEY (`created_by`) REFERENCES `user` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `intervention_ibfk_6` FOREIGN KEY (`updated_by`) REFERENCES `user` (`id`) ON DELETE SET NULL;

--
-- Contraintes pour la table `intervention_class`
--
ALTER TABLE `intervention_class`
  ADD CONSTRAINT `intervention_class_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `user` (`id`) ON DELETE SET NULL;

--
-- Contraintes pour la table `intervention_cost`
--
ALTER TABLE `intervention_cost`
  ADD CONSTRAINT `intervention_cost_ibfk_1` FOREIGN KEY (`intervention_id`) REFERENCES `intervention` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `intervention_entity`
--
ALTER TABLE `intervention_entity`
  ADD CONSTRAINT `intervention_entity_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `user` (`id`) ON DELETE SET NULL;

--
-- Contraintes pour la table `intervention_personnel`
--
ALTER TABLE `intervention_personnel`
  ADD CONSTRAINT `intervention_personnel_ibfk_1` FOREIGN KEY (`intervention_id`) REFERENCES `intervention` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `intervention_personnel_ibfk_2` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `intervention_stock`
--
ALTER TABLE `intervention_stock`
  ADD CONSTRAINT `intervention_stock_ibfk_1` FOREIGN KEY (`intervention_id`) REFERENCES `intervention` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `intervention_stock_ibfk_2` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_item` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `intervention_type`
--
ALTER TABLE `intervention_type`
  ADD CONSTRAINT `intervention_type_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `user` (`id`) ON DELETE SET NULL;

--
-- Contraintes pour la table `notification`
--
ALTER TABLE `notification`
  ADD CONSTRAINT `notification_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `notification_ibfk_2` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_item` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `notification_ibfk_3` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`) ON DELETE SET NULL;

--
-- Contraintes pour la table `project`
--
ALTER TABLE `project`
  ADD CONSTRAINT `fk_project_client` FOREIGN KEY (`client_id`) REFERENCES `client` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Contraintes pour la table `project_file`
--
ALTER TABLE `project_file`
  ADD CONSTRAINT `project_file_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `stock_attribute`
--
ALTER TABLE `stock_attribute`
  ADD CONSTRAINT `stock_attribute_ibfk_1` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_item` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `stock_file`
--
ALTER TABLE `stock_file`
  ADD CONSTRAINT `stock_file_ibfk_1` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_item` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `stock_item`
--
ALTER TABLE `stock_item`
  ADD CONSTRAINT `stock_item_ibfk_1` FOREIGN KEY (`supplier_id`) REFERENCES `supplier` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `stock_item_ibfk_2` FOREIGN KEY (`category_id`) REFERENCES `stock_category` (`id`) ON DELETE SET NULL;

--
-- Contraintes pour la table `task`
--
ALTER TABLE `task`
  ADD CONSTRAINT `task_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `task_ibfk_2` FOREIGN KEY (`task_type_id`) REFERENCES `task_type` (`id`) ON DELETE SET NULL;

--
-- Contraintes pour la table `task_groups`
--
ALTER TABLE `task_groups`
  ADD CONSTRAINT `task_groups_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `task_groups_ibfk_2` FOREIGN KEY (`group_id`) REFERENCES `group` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `task_personnel`
--
ALTER TABLE `task_personnel`
  ADD CONSTRAINT `task_personnel_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `task_personnel_ibfk_2` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `task_stock_item`
--
ALTER TABLE `task_stock_item`
  ADD CONSTRAINT `task_stock_item_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `task_stock_item_ibfk_2` FOREIGN KEY (`stock_item_id`) REFERENCES `stock_item` (`id`) ON DELETE SET NULL;

--
-- Contraintes pour la table `user`
--
ALTER TABLE `user`
  ADD CONSTRAINT `user_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
