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

CREATE TABLE IF NOT EXISTS usuarios (
  id_usuario BIGINT NOT NULL AUTO_INCREMENT,
  id_rol CHAR(8) NOT NULL,
  rol ENUM('Administrador/a', 'Selector', 'Comunicador') NOT NULL,
  correo VARCHAR(150) NOT NULL,
  nombre_completo VARCHAR(150) NOT NULL,
  id_centro INT NOT NULL,
  id_centro_satelite INT NULL,
  anexo_telefono VARCHAR(20) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,

  PRIMARY KEY (id_usuario),

  INDEX idx_usuarios_correo (correo),
  INDEX idx_usuarios_rol (rol),
  INDEX idx_usuarios_centro (id_centro),
  INDEX idx_usuarios_centro_satelite (id_centro_satelite),

  CONSTRAINT fk_usuarios_centro
    FOREIGN KEY (id_centro)
    REFERENCES centros(id_centro)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_usuarios_centro_satelite
    FOREIGN KEY (id_centro_satelite)
    REFERENCES centros(id_centro)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS solicitudes_solicitud (
  id_solicitud BIGINT NOT NULL AUTO_INCREMENT,
  rut VARCHAR(12) NOT NULL,
  nombre_completo VARCHAR(150) NOT NULL,
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

  INDEX idx_solicitud_rut (rut),
  INDEX idx_solicitud_centro_fecha (id_centro, date_solicitud),
  INDEX idx_solicitud_prioridad (priorizacion_solicitud, puntaje_prioridad),

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
    )),

  CONSTRAINT chk_solicitud_otro
    CHECK (
      Neurodivergente_prais_gestante_tipo <> 'OTRO'
      OR Neurodivergente_prais_gestante_otro <> ''
    )
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS selector_demanda (
  id_seleccion BIGINT NOT NULL AUTO_INCREMENT,
  id_solicitud BIGINT NOT NULL,
  id_usuario_selector BIGINT NULL,
  rut_selector VARCHAR(12) NULL,
  fecha_accion DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  clasificacion VARCHAR(50) NULL,
  prioridad VARCHAR(8) NULL,
  suma_prioridad SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  observacion LONGTEXT NULL,

  PRIMARY KEY (id_seleccion),

  INDEX idx_selector_solicitud (id_solicitud),
  INDEX idx_selector_usuario (id_usuario_selector),
  INDEX idx_selector_fecha (fecha_accion),
  INDEX idx_selector_prioridad (prioridad),

  CONSTRAINT fk_selector_solicitud
    FOREIGN KEY (id_solicitud)
    REFERENCES solicitudes_solicitud(id_solicitud)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_selector_usuario
    FOREIGN KEY (id_usuario_selector)
    REFERENCES usuarios(id_usuario)
    ON UPDATE CASCADE
    ON DELETE SET NULL,

  CONSTRAINT chk_selector_prioridad
    CHECK (
      prioridad IS NULL
      OR prioridad IN ('URGENTE', 'ALTA', 'MEDIA', 'BAJA')
    )
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS comunicador_seleccion (
  id_comunicador BIGINT NOT NULL AUTO_INCREMENT,
  id_seleccion BIGINT NOT NULL,
  id_usuario_comunicador BIGINT NULL,
  rut_comunicador VARCHAR(12) NULL,
  estado VARCHAR(16) NOT NULL DEFAULT 'PENDIENTE',
  fecha_hora_agendamiento DATETIME(6) NULL,
  enviado BOOLEAN NOT NULL DEFAULT FALSE,

  PRIMARY KEY (id_comunicador),

  INDEX idx_comunicador_seleccion (id_seleccion),
  INDEX idx_comunicador_usuario (id_usuario_comunicador),
  INDEX idx_comunicador_estado (estado),
  INDEX idx_comunicador_agendamiento (fecha_hora_agendamiento),

  CONSTRAINT fk_comunicador_selector
    FOREIGN KEY (id_seleccion)
    REFERENCES selector_demanda(id_seleccion)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_comunicador_usuario
    FOREIGN KEY (id_usuario_comunicador)
    REFERENCES usuarios(id_usuario)
    ON UPDATE CASCADE
    ON DELETE SET NULL,

  CONSTRAINT chk_comunicador_estado
    CHECK (
      estado IN (
        'PENDIENTE',
        'CONTACTADO',
        'AGENDADO',
        'NO_CONTACTADO',
        'RECHAZADO',
        'FINALIZADO'
      )
    )
) ENGINE=InnoDB;
