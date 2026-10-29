# Reporte de Análisis Taxonómico de URLs - public.cleansed_programs

## 1. Resumen General
- **Total de registros analizados:** 659

### Distribución por Institución (Dominio)
```
ucontinental.edu.pe    |   388
 www.up.edu.pe          |   113
 www.newhorizons.edu.pe |    78
 dmc.pe                 |    39
 www.utp.edu.pe         |    20
 www.senati.edu.pe      |    14
 www.pucp.edu.pe        |     7
```

## 2. Top 25 Segmentos de Ruta (Global)
Estos son los términos que más se repiten en cualquier nivel de la URL.
```
noticias                                 |       274
 eventos                                  |        87
 egp                                      |        83
 cursos-y-certificaciones-internacionales |        78
 maestrias                                |        50
 programas-especializacion                |        26
 producto                                 |        26
 plana-docente                            |        19
 presentacion                             |        18
 medios                                   |        18
 beneficios                               |        16
 ciberseguridad                           |        14
 gestion-y-procesos-de-ti                 |        13
 Paginas                                  |        12
 cursos                                   |        10
 carreras-postgrado-idiomas               |        10
 sustentacion-tesis                       |        10
 convocatorias-investigacion              |        10
 prensa                                   |        10
 web                                      |        10
 carreras-pregrado                        |        10
 idiomas                                  |         9
 curso-actualizacion.aspx                 |         9
 admision                                 |         8
 ia-agilidad-e-innovacion                 |         7
```

## 3. Análisis por Niveles de Ruta

### Nivel 1 (Top 10)
```
noticias                                 |       272
 egp                                      |        83
 eventos                                  |        78
 cursos-y-certificaciones-internacionales |        78
 producto                                 |        26
 medios                                   |        18
 web                                      |        10
 cursos                                   |        10
 prensa                                   |        10
 carreras-postgrado-idiomas               |        10
```

### Nivel 2 (Top 10)
```
maestrias                   |        50
 programas-especializacion   |        26
 ciberseguridad              |        14
 gestion-y-procesos-de-ti    |        13
 convocatorias-investigacion |        10
 carreras-pregrado           |        10
 eventos                     |         9
 ia-agilidad-e-innovacion    |         7
 gestion-de-proyectos        |         6
 cloud                       |         6
```

### Nivel 3 (Top 10)
```
gestion-publica-regular                                |         6
 maestria-politicas-publicas                            |         6
 gestion-inversion-social                               |         6
 economia-aplicada                                      |         5
 gestion-publica-descentralizada                        |         5
 economia                                               |         5
 regulacion-servicios-publicos-gestion-infraestructuras |         5
 derecho-administrativo-economico                       |         5
 direccion-de-proyectos-programas-sociales              |         4
 gestion-publica                                        |         4
```

## 4. Categorización Semántica (Agrupación Estructural)
Frecuencia de URLs que contienen términos clave en sus rutas:
- **Postgrado / Maestrías**: 71
- **Cursos / Certificaciones**: 371
- **Diplomados / Especializaciones**: 90
- **Pregrado**: 15
- **Contenido Informativo (Noticias/Eventos)**: 367

## 5. Observaciones Técnicas
1. **Predominancia de Noticias:** Una gran parte de la tabla `cleansed_programs` (aprox. 40-50%) parece contener URLs de tipo informativo ('noticias', 'eventos'), lo cual sugiere que el proceso de limpieza o recolección original incluyó feeds de noticias de las instituciones.
2. **Estructura por Institución:**
   - `www.up.edu.pe` utiliza mayormente `/egp/` (Escuela de Gestión Pública) para sus programas.
   - `www.newhorizons.edu.pe` utiliza `/cursos-y-certificaciones-internacionales/` como raíz.
   - `dmc.pe` utiliza `/producto/` para sus especializaciones.
3. **Nivel de Maestrías:** Las maestrías suelen aparecer en el segundo nivel de profundidad (`/egp/maestrias/...`).