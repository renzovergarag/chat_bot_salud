CREATE DATABASE IF NOT EXISTS chat_bot_salud
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE chat_bot_salud;

CREATE TABLE IF NOT EXISTS centros (
  id_centro INT NOT NULL,
  centro VARCHAR(150) NOT NULL,

  PRIMARY KEY (id_centro),
  UNIQUE KEY uq_centros_nombre (centro)
) ENGINE=InnoDB;

INSERT INTO centros (id_centro, centro) VALUES
(600, 'Centro De Salud Familiar Laguna Verde'),
(605, 'Centro De Salud Familiar Placilla (Valparaiso)'),
(610, 'Centro De Salud Familiar Placeres'),
(615, 'Centro De Salud Familiar Baron'),
(620, 'Centro De Salud Familiar Rodelillo'),
(621, 'Centro De Salud Familiar Padre Damian Molokai'),
(625, 'Centro De Salud Familiar Quebrada Verde'),
(626, 'Centro Comunitario De Salud Familiar Porvenir Bajo'),
(627, 'Centro Comunitario De Salud Familiar Juan Pablo II'),
(630, 'Centro De Salud Familiar Las Canas'),
(635, 'Centro De Salud Familiar Mena'),
(640, 'Centro De Salud Familiar Puertas Negras'),
(645, 'Centro De Salud Familiar Cordillera'),
(650, 'Centro De Salud Familiar Esperanza'),
(655, 'Centro De Salud Familiar Reina Isabel II')
ON DUPLICATE KEY UPDATE
  centro = VALUES(centro);

CREATE TABLE IF NOT EXISTS solicitudes_solicitud (
  id_solicitud BIGINT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(150) NOT NULL DEFAULT '',
  rut VARCHAR(12) NOT NULL,
  edad SMALLINT UNSIGNED NOT NULL,
  sexo VARCHAR(1) NOT NULL DEFAULT 'N',
  telefono VARCHAR(12) NOT NULL,
  id_centro INT NOT NULL,
  credendencial_cuidador_discapacidad BOOLEAN NOT NULL DEFAULT FALSE,
  credencial_cuidador_discapacidad_foto LONGTEXT NOT NULL,
  Neurodivergente_prais_gestante BOOLEAN NOT NULL DEFAULT FALSE,
  Neurodivergente_prais_gestante_tipo VARCHAR(32) NOT NULL DEFAULT '',
  Neurodivergente_prais_gestante_otro VARCHAR(50) NOT NULL DEFAULT '',
  acepta_terminos BOOLEAN NOT NULL DEFAULT FALSE,
  motivo VARCHAR(160) NOT NULL,
  detalle_motivo LONGTEXT NOT NULL,
  fecha_solicitud DATE NOT NULL,
  date_solicitud DATETIME(6) NOT NULL,
  priorizacion_solicitud VARCHAR(8) NOT NULL DEFAULT 'BAJA',
  puntaje_prioridad SMALLINT UNSIGNED NOT NULL DEFAULT 0,

  PRIMARY KEY (id_solicitud),

  CONSTRAINT fk_solicitud_centro
    FOREIGN KEY (id_centro)
    REFERENCES centros(id_centro)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT chk_solicitud_edad
    CHECK (edad BETWEEN 0 AND 120),

  CONSTRAINT chk_solicitud_sexo
    CHECK (sexo IN ('F', 'M', 'O', 'N')),

  CONSTRAINT chk_solicitud_prioridad
    CHECK (priorizacion_solicitud IN ('URGENTE', 'ALTA', 'MEDIA', 'BAJA')),

  CONSTRAINT chk_solicitud_tipo_condicion
    CHECK (Neurodivergente_prais_gestante_tipo IN (
      '',
      'NEURODIVERGENTE',
      'CUIDADOR_NEURODIVERGENTE',
      'PRAIS',
      'GESTANTE',
      'OTRO'
    ))
) ENGINE=InnoDB;

CREATE INDEX idx_solicitud_rut
  ON solicitudes_solicitud (rut);

CREATE INDEX idx_solicitud_centro_fecha
  ON solicitudes_solicitud (id_centro, date_solicitud);

CREATE INDEX idx_solicitud_prioridad
  ON solicitudes_solicitud (priorizacion_solicitud, puntaje_prioridad);
