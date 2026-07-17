CREATE DATABASE IF NOT EXISTS chat_bot_salud
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE chat_bot_salud;

CREATE TABLE IF NOT EXISTS solicitudes_solicitud (
  id_solicitud BIGINT NOT NULL AUTO_INCREMENT,
  rut VARCHAR(12) NOT NULL,
  edad SMALLINT UNSIGNED NOT NULL,
  sexo VARCHAR(1) NOT NULL DEFAULT 'N',
  telefono VARCHAR(12) NOT NULL,
  centro_salud VARCHAR(3) NOT NULL,
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

  CONSTRAINT chk_solicitud_edad
    CHECK (edad BETWEEN 0 AND 120),

  CONSTRAINT chk_solicitud_sexo
    CHECK (sexo IN ('F', 'M', 'O', 'N')),

  CONSTRAINT chk_solicitud_centro_salud
    CHECK (centro_salud IN (
      '600','605','610','615','620','621','625',
      '630','635','640','645','650','655'
    )),

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
);

CREATE INDEX idx_solicitud_rut
  ON solicitudes_solicitud (rut);

CREATE INDEX idx_solicitud_centro_fecha
  ON solicitudes_solicitud (centro_salud, date_solicitud);

CREATE INDEX idx_solicitud_prioridad
  ON solicitudes_solicitud (priorizacion_solicitud, puntaje_prioridad);
