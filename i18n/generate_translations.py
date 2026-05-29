#!/usr/bin/env python3
"""
Generate .ts translation files for Tomofast-x-q plugin.
Run this script from the i18n folder, then compile with:
    lrelease *.ts
or use the QGIS plugin builder compile-strings script.
"""
import os

CONTEXT = "mQgsSpinBox_mesh_south_2"
UI_FILE = "ui_dockwidget_generated.py"

# Source strings -> translations per language
# Format: { source_string: { lang_code: translation } }
TRANSLATIONS = {
    "Tomofast_x": {
        "fr": "Tomofast_x", "es": "Tomofast_x", "pt": "Tomofast_x",
        "pt_BR": "Tomofast_x", "zh": "Tomofast_x",
    },
    "Step 1 : Inversion type": {
        "fr": "Étape 1 : Type d'inversion",
        "es": "Paso 1 : Tipo de inversión",
        "pt": "Etapa 1 : Tipo de inversão",
        "pt_BR": "Etapa 1 : Tipo de inversão",
        "zh": "步骤1：反演类型",
    },
    "Gravity": {
        "fr": "Gravimétrie", "es": "Gravimetría",
        "pt": "Gravimetria", "pt_BR": "Gravimetria", "zh": "重力",
    },
    "Mag": {
        "fr": "Magnétique", "es": "Magnético",
        "pt": "Magnético", "pt_BR": "Magnético", "zh": "磁力",
    },
    "Joint": {
        "fr": "Joint", "es": "Conjunto",
        "pt": "Conjunto", "pt_BR": "Conjunto", "zh": "联合",
    },
    "Step 2a : Select the gravity data file": {
        "fr": "Étape 2a : Sélectionner le fichier de données gravimétriques",
        "es": "Paso 2a : Seleccionar el archivo de datos de gravedad",
        "pt": "Etapa 2a : Selecionar o arquivo de dados gravimétricos",
        "pt_BR": "Etapa 2a : Selecionar o arquivo de dados gravimétricos",
        "zh": "步骤2a：选择重力数据文件",
    },
    "Data layer:": {
        "fr": "Couche de données :", "es": "Capa de datos:",
        "pt": "Camada de dados:", "pt_BR": "Camada de dados:", "zh": "数据图层：",
    },
    "path to grav data file": {
        "fr": "chemin vers le fichier de données gravimétriques",
        "es": "ruta al archivo de datos de gravedad",
        "pt": "caminho para o arquivo de dados gravimétricos",
        "pt_BR": "caminho para o arquivo de dados gravimétricos",
        "zh": "重力数据文件路径",
    },
    "Input CRS": {
        "fr": "SCR d'entrée", "es": "CRS de entrada",
        "pt": "SRC de entrada", "pt_BR": "SRC de entrada", "zh": "输入坐标系",
    },
    "Output CRS": {
        "fr": "SCR de sortie", "es": "CRS de salida",
        "pt": "SRC de saída", "pt_BR": "SRC de saída", "zh": "输出坐标系",
    },
    "Load Grav": {
        "fr": "Charger Grav", "es": "Cargar Grav",
        "pt": "Carregar Grav", "pt_BR": "Carregar Grav", "zh": "加载重力",
    },
    "Step 2b : Define grav input fields": {
        "fr": "Étape 2b : Définir les champs d'entrée gravimétriques",
        "es": "Paso 2b : Definir campos de entrada de gravedad",
        "pt": "Etapa 2b : Definir campos de entrada gravimétricos",
        "pt_BR": "Etapa 2b : Definir campos de entrada gravimétricos",
        "zh": "步骤2b：定义重力输入字段",
    },
    "long_x": {
        "fr": "long_x", "es": "long_x",
        "pt": "long_x", "pt_BR": "long_x", "zh": "经度_x",
    },
    "lat_y": {
        "fr": "lat_y", "es": "lat_y",
        "pt": "lat_y", "pt_BR": "lat_y", "zh": "纬度_y",
    },
    "Data Column": {
        "fr": "Colonne de données", "es": "Columna de datos",
        "pt": "Coluna de dados", "pt_BR": "Coluna de dados", "zh": "数据列",
    },
    "Assign fields": {
        "fr": "Assigner les champs", "es": "Asignar campos",
        "pt": "Atribuir campos", "pt_BR": "Atribuir campos", "zh": "分配字段",
    },
    "Step 5 : Specify Mesh Parameters": {
        "fr": "Étape 5 : Spécifier les paramètres du maillage",
        "es": "Paso 5 : Especificar parámetros de malla",
        "pt": "Etapa 5 : Especificar parâmetros de malha",
        "pt_BR": "Etapa 5 : Especificar parâmetros de malha",
        "zh": "步骤5：指定网格参数",
    },
    "Cell Size y": {
        "fr": "Taille de cellule y", "es": "Tamaño de celda y",
        "pt": "Tamanho da célula y", "pt_BR": "Tamanho da célula y", "zh": "单元大小 y",
    },
    "Horizontal Padding": {
        "fr": "Rembourrage horizontal", "es": "Relleno horizontal",
        "pt": "Preenchimento horizontal", "pt_BR": "Preenchimento horizontal", "zh": "水平填充",
    },
    "Cell Size x": {
        "fr": "Taille de cellule x", "es": "Tamaño de celda x",
        "pt": "Tamanho da célula x", "pt_BR": "Tamanho da célula x", "zh": "单元大小 x",
    },
    "West": {
        "fr": "Ouest", "es": "Oeste",
        "pt": "Oeste", "pt_BR": "Oeste", "zh": "西",
    },
    "South": {
        "fr": "Sud", "es": "Sur",
        "pt": "Sul", "pt_BR": "Sul", "zh": "南",
    },
    "Horizontal Cell Dimensions": {
        "fr": "Dimensions horizontales des cellules",
        "es": "Dimensiones horizontales de celda",
        "pt": "Dimensões horizontais da célula",
        "pt_BR": "Dimensões horizontais da célula",
        "zh": "水平单元尺寸",
    },
    "East": {
        "fr": "Est", "es": "Este",
        "pt": "Leste", "pt_BR": "Leste", "zh": "东",
    },
    "North": {
        "fr": "Nord", "es": "Norte",
        "pt": "Norte", "pt_BR": "Norte", "zh": "北",
    },
    "# Cells": {
        "fr": "# Cellules", "es": "# Celdas",
        "pt": "# Células", "pt_BR": "# Células", "zh": "单元数",
    },
    "Core Cell Size z": {
        "fr": "Taille de cellule centrale z", "es": "Tamaño de celda núcleo z",
        "pt": "Tamanho da célula núcleo z", "pt_BR": "Tamanho da célula núcleo z", "zh": "核心单元大小 z",
    },
    "Define Mesh x,y Limits by shapefile": {
        "fr": "Définir les limites x,y du maillage par shapefile",
        "es": "Definir límites x,y de la malla por shapefile",
        "pt": "Definir limites x,y da malha por shapefile",
        "pt_BR": "Definir limites x,y da malha por shapefile",
        "zh": "通过shapefile定义网格x,y范围",
    },
    "Full Depth": {
        "fr": "Profondeur totale", "es": "Profundidad total",
        "pt": "Profundidade total", "pt_BR": "Profundidade total", "zh": "总深度",
    },
    "Core Depth": {
        "fr": "Profondeur centrale", "es": "Profundidad núcleo",
        "pt": "Profundidade núcleo", "pt_BR": "Profundidade núcleo", "zh": "核心深度",
    },
    "Use Compression": {
        "fr": "Utiliser la compression", "es": "Usar compresión",
        "pt": "Usar compressão", "pt_BR": "Usar compressão", "zh": "使用压缩",
    },
    "Rate": {
        "fr": "Taux", "es": "Tasa",
        "pt": "Taxa", "pt_BR": "Taxa", "zh": "比率",
    },
    "Estimated Memory Requirement (GB)": {
        "fr": "Mémoire estimée requise (Go)",
        "es": "Memoria estimada requerida (GB)",
        "pt": "Memória estimada necessária (GB)",
        "pt_BR": "Memória estimada necessária (GB)",
        "zh": "预估内存需求 (GB)",
    },
    "z cell size \nlist": {
        "fr": "Liste tailles\ncellules z", "es": "Lista tamaño\nceldas z",
        "pt": "Lista tamanhos\ncélulas z", "pt_BR": "Lista tamanhos\ncélulas z", "zh": "z单元大小\n列表",
    },
    "z cell layer\nthickness list": {
        "fr": "Liste épaisseurs\ncouches z", "es": "Lista espesores\ncapas z",
        "pt": "Lista espessuras\ncamadas z", "pt_BR": "Lista espessuras\ncamadas z", "zh": "z层\n厚度列表",
    },
    "OR": {
        "fr": "OU", "es": "O",
        "pt": "OU", "pt_BR": "OU", "zh": "或",
    },
    "Step 3a : Select the magnetics data file": {
        "fr": "Étape 3a : Sélectionner le fichier de données magnétiques",
        "es": "Paso 3a : Seleccionar el archivo de datos magnéticos",
        "pt": "Etapa 3a : Selecionar o arquivo de dados magnéticos",
        "pt_BR": "Etapa 3a : Selecionar o arquivo de dados magnéticos",
        "zh": "步骤3a：选择磁力数据文件",
    },
    "Load Mag": {
        "fr": "Charger Mag", "es": "Cargar Mag",
        "pt": "Carregar Mag", "pt_BR": "Carregar Mag", "zh": "加载磁力",
    },
    "Path to mag data file": {
        "fr": "Chemin vers le fichier de données magnétiques",
        "es": "Ruta al archivo de datos magnéticos",
        "pt": "Caminho para o arquivo de dados magnéticos",
        "pt_BR": "Caminho para o arquivo de dados magnéticos",
        "zh": "磁力数据文件路径",
    },
    "Step 3b : Define mag input fields": {
        "fr": "Étape 3b : Définir les champs d'entrée magnétiques",
        "es": "Paso 3b : Definir campos de entrada magnéticos",
        "pt": "Etapa 3b : Definir campos de entrada magnéticos",
        "pt_BR": "Etapa 3b : Definir campos de entrada magnéticos",
        "zh": "步骤3b：定义磁力输入字段",
    },
    "lat/y": {
        "fr": "lat/y", "es": "lat/y",
        "pt": "lat/y", "pt_BR": "lat/y", "zh": "纬度/y",
    },
    "Data": {
        "fr": "Données", "es": "Datos",
        "pt": "Dados", "pt_BR": "Dados", "zh": "数据",
    },
    "long/x": {
        "fr": "long/x", "es": "long/x",
        "pt": "long/x", "pt_BR": "long/x", "zh": "经度/x",
    },
    "Step 4 : Select DTM (optional)": {
        "fr": "Étape 4 : Sélectionner le MNT (optionnel)",
        "es": "Paso 4 : Seleccionar DTM (opcional)",
        "pt": "Etapa 4 : Selecionar DTM (opcional)",
        "pt_BR": "Etapa 4 : Selecionar DTM (opcional)",
        "zh": "步骤4：选择DTM（可选）",
    },
    "Path to DTM file": {
        "fr": "Chemin vers le fichier MNT",
        "es": "Ruta al archivo DTM",
        "pt": "Caminho para o arquivo DTM",
        "pt_BR": "Caminho para o arquivo DTM",
        "zh": "DTM文件路径",
    },
    "Step 0 : Load existing Parameter File (optional)": {
        "fr": "Étape 0 : Charger un fichier de paramètres existant (optionnel)",
        "es": "Paso 0 : Cargar archivo de parámetros existente (opcional)",
        "pt": "Etapa 0 : Carregar arquivo de parâmetros existente (opcional)",
        "pt_BR": "Etapa 0 : Carregar arquivo de parâmetros existente (opcional)",
        "zh": "步骤0：加载已有参数文件（可选）",
    },
    "Path to exisiting parameter file": {
        "fr": "Chemin vers le fichier de paramètres existant",
        "es": "Ruta al archivo de parámetros existente",
        "pt": "Caminho para o arquivo de parâmetros existente",
        "pt_BR": "Caminho para o arquivo de parâmetros existente",
        "zh": "已有参数文件路径",
    },
    "Continue on to Grav/Mag Parameters Tab...": {
        "fr": "Continuer vers l'onglet Paramètres Grav/Mag...",
        "es": "Continuar a la pestaña Parámetros Grav/Mag...",
        "pt": "Continuar para a aba Parâmetros Grav/Mag...",
        "pt_BR": "Continuar para a aba Parâmetros Grav/Mag...",
        "zh": "继续前往重力/磁力参数选项卡...",
    },
    "Reset Dialog": {
        "fr": "Réinitialiser", "es": "Restablecer",
        "pt": "Redefinir", "pt_BR": "Redefinir", "zh": "重置",
    },
    "Data/Mesh": {
        "fr": "Données/Maillage", "es": "Datos/Malla",
        "pt": "Dados/Malha", "pt_BR": "Dados/Malha", "zh": "数据/网格",
    },
    "Mag  Model Damping (m - m_prior)": {
        "fr": "Amortissement modèle Mag (m - m_prior)",
        "es": "Amortiguación modelo Mag (m - m_prior)",
        "pt": "Amortecimento modelo Mag (m - m_prior)",
        "pt_BR": "Amortecimento modelo Mag (m - m_prior)",
        "zh": "磁力模型阻尼 (m - m_prior)",
    },
    "Weight": {
        "fr": "Poids", "es": "Peso",
        "pt": "Peso", "pt_BR": "Peso", "zh": "权重",
    },
    "Norm Power": {
        "fr": "Puissance norme", "es": "Potencia norma",
        "pt": "Potência norma", "pt_BR": "Potência norma", "zh": "范数幂次",
    },
    "Gravity Parameters": {
        "fr": "Paramètres gravimétriques", "es": "Parámetros de gravedad",
        "pt": "Parâmetros gravimétricos", "pt_BR": "Parâmetros gravimétricos", "zh": "重力参数",
    },
    "Grav Unit Multipliers": {
        "fr": "Multiplicateurs d'unités Grav",
        "es": "Multiplicadores de unidades Grav",
        "pt": "Multiplicadores de unidades Grav",
        "pt_BR": "Multiplicadores de unidades Grav",
        "zh": "重力单位乘数",
    },
    "Data ": {
        "fr": "Données ", "es": "Datos ",
        "pt": "Dados ", "pt_BR": "Dados ", "zh": "数据 ",
    },
    "Model": {
        "fr": "Modèle", "es": "Modelo",
        "pt": "Modelo", "pt_BR": "Modelo", "zh": "模型",
    },
    "Magnetics Parameters": {
        "fr": "Paramètres magnétiques", "es": "Parámetros magnéticos",
        "pt": "Parâmetros magnéticos", "pt_BR": "Parâmetros magnéticos", "zh": "磁力参数",
    },
    "Grav Model Damping (m - m_prior)": {
        "fr": "Amortissement modèle Grav (m - m_prior)",
        "es": "Amortiguación modelo Grav (m - m_prior)",
        "pt": "Amortecimento modelo Grav (m - m_prior)",
        "pt_BR": "Amortecimento modelo Grav (m - m_prior)",
        "zh": "重力模型阻尼 (m - m_prior)",
    },
    "Mag Unit Multipliers": {
        "fr": "Multiplicateurs d'unités Mag",
        "es": "Multiplicadores de unidades Mag",
        "pt": "Multiplicadores de unidades Mag",
        "pt_BR": "Multiplicadores de unidades Mag",
        "zh": "磁力单位乘数",
    },
    "Mag ADMM Constraints": {
        "fr": "Contraintes ADMM Mag", "es": "Restricciones ADMM Mag",
        "pt": "Restrições ADMM Mag", "pt_BR": "Restrições ADMM Mag", "zh": "磁力ADMM约束",
    },
    "Mag Bounds (space\n separated pairs)": {
        "fr": "Limites Mag (paires\n séparées par espace)",
        "es": "Límites Mag (pares\n separados por espacio)",
        "pt": "Limites Mag (pares\n separados por espaço)",
        "pt_BR": "Limites Mag (pares\n separados por espaço)",
        "zh": "磁力边界（空格\n分隔的对）",
    },
    "No Lithologies": {
        "fr": "Nombre de lithologies", "es": "N.º de litologías",
        "pt": "N.º de litologias", "pt_BR": "N.º de litologias", "zh": "岩性数量",
    },
    "Grav ADMM Constraints": {
        "fr": "Contraintes ADMM Grav", "es": "Restricciones ADMM Grav",
        "pt": "Restrições ADMM Grav", "pt_BR": "Restrições ADMM Grav", "zh": "重力ADMM约束",
    },
    "Grav Bounds (space \nseparated pairs)": {
        "fr": "Limites Grav (paires\n séparées par espace)",
        "es": "Límites Grav (pares\n separados por espacio)",
        "pt": "Limites Grav (pares\n separados por espaço)",
        "pt_BR": "Limites Grav (pares\n separados por espaço)",
        "zh": "重力边界（空格\n分隔的对）",
    },
    "Grav Bounds (space\n separated pairs)": {
        "fr": "Limites Grav (paires\n séparées par espace)",
        "es": "Límites Grav (pares\n separados por espacio)",
        "pt": "Limites Grav (pares\n separados por espaço)",
        "pt_BR": "Limites Grav (pares\n separados por espaço)",
        "zh": "重力边界（空格\n分隔的对）",
    },
    "Continue on to Global Parameters Tab...": {
        "fr": "Continuer vers l'onglet Paramètres globaux...",
        "es": "Continuar a la pestaña Parámetros globales...",
        "pt": "Continuar para a aba Parâmetros globais...",
        "pt_BR": "Continuar para a aba Parâmetros globais...",
        "zh": "继续前往全局参数选项卡...",
    },
    "Magnetic Field Parameters": {
        "fr": "Paramètres du champ magnétique",
        "es": "Parámetros del campo magnético",
        "pt": "Parâmetros do campo magnético",
        "pt_BR": "Parâmetros do campo magnético",
        "zh": "磁场参数",
    },
    "Declination": {
        "fr": "Déclinaison", "es": "Declinación",
        "pt": "Declinação", "pt_BR": "Declinação", "zh": "磁偏角",
    },
    "Inclination": {
        "fr": "Inclinaison", "es": "Inclinación",
        "pt": "Inclinação", "pt_BR": "Inclinação", "zh": "磁倾角",
    },
    "Intensity": {
        "fr": "Intensité", "es": "Intensidad",
        "pt": "Intensidade", "pt_BR": "Intensidade", "zh": "强度",
    },
    "Calculate from Survey Parameters": {
        "fr": "Calculer depuis les paramètres du relevé",
        "es": "Calcular desde parámetros del levantamiento",
        "pt": "Calcular a partir dos parâmetros do levantamento",
        "pt_BR": "Calcular a partir dos parâmetros do levantamento",
        "zh": "从测量参数计算",
    },
    "Mag Survey \nDay/Month/Year": {
        "fr": "Relevé Mag\nJour/Mois/Année",
        "es": "Levantamiento Mag\nDía/Mes/Año",
        "pt": "Levantamento Mag\nDia/Mês/Ano",
        "pt_BR": "Levantamento Mag\nDia/Mês/Ano",
        "zh": "磁力测量\n日/月/年",
    },
    "Sensor Height": {
        "fr": "Hauteur du capteur", "es": "Altura del sensor",
        "pt": "Altura do sensor", "pt_BR": "Altura do sensor", "zh": "传感器高度",
    },
    "Survey Parameters": {
        "fr": "Paramètres du relevé", "es": "Parámetros del levantamiento",
        "pt": "Parâmetros do levantamento", "pt_BR": "Parâmetros do levantamento", "zh": "测量参数",
    },
    "Grav/Mag Parameters": {
        "fr": "Paramètres Grav/Mag", "es": "Parámetros Grav/Mag",
        "pt": "Parâmetros Grav/Mag", "pt_BR": "Parâmetros Grav/Mag", "zh": "重力/磁力参数",
    },
    "Experiment Parameters": {
        "fr": "Paramètres de l'expérience", "es": "Parámetros del experimento",
        "pt": "Parâmetros do experimento", "pt_BR": "Parâmetros do experimento", "zh": "实验参数",
    },
    "Inversion Experiment": {
        "fr": "Expérience d'inversion", "es": "Experimento de inversión",
        "pt": "Experimento de inversão", "pt_BR": "Experimento de inversão", "zh": "反演实验",
    },
    "Description": {
        "fr": "Description", "es": "Descripción",
        "pt": "Descrição", "pt_BR": "Descrição", "zh": "描述",
    },
    "Global Parameters": {
        "fr": "Paramètres globaux", "es": "Parámetros globales",
        "pt": "Parâmetros globais", "pt_BR": "Parâmetros globais", "zh": "全局参数",
    },
    "Sensitivity Kernel": {
        "fr": "Noyau de sensibilité", "es": "Núcleo de sensibilidad",
        "pt": "Núcleo de sensibilidade", "pt_BR": "Núcleo de sensibilidade", "zh": "灵敏度核",
    },
    "Read from File": {
        "fr": "Lire depuis un fichier", "es": "Leer desde archivo",
        "pt": "Ler de arquivo", "pt_BR": "Ler de arquivo", "zh": "从文件读取",
    },
    "Choose your Main Project ": {
        "fr": "Choisissez votre projet principal ",
        "es": "Elija su proyecto principal ",
        "pt": "Escolha o seu projeto principal ",
        "pt_BR": "Escolha o seu projeto principal ",
        "zh": "选择主项目 ",
    },
    "Inversion Parameters": {
        "fr": "Paramètres d'inversion", "es": "Parámetros de inversión",
        "pt": "Parâmetros de inversão", "pt_BR": "Parâmetros de inversão", "zh": "反演参数",
    },
    "Major Iterations": {
        "fr": "Itérations majeures", "es": "Iteraciones principales",
        "pt": "Iterações principais", "pt_BR": "Iterações principais", "zh": "主迭代次数",
    },
    "Minor Iterations": {
        "fr": "Itérations mineures", "es": "Iteraciones secundarias",
        "pt": "Iterações secundárias", "pt_BR": "Iterações secundárias", "zh": "次迭代次数",
    },
    "Model save iter": {
        "fr": "Sauvegarder modèle iter.", "es": "Guardar modelo iter.",
        "pt": "Salvar modelo iter.", "pt_BR": "Salvar modelo iter.", "zh": "模型保存间隔",
    },
    "min Residual": {
        "fr": "Résidu minimum", "es": "Residuo mínimo",
        "pt": "Resíduo mínimo", "pt_BR": "Resíduo mínimo", "zh": "最小残差",
    },
    "Target Misfit": {
        "fr": "Erreur cible", "es": "Error objetivo",
        "pt": "Erro alvo", "pt_BR": "Erro alvo", "zh": "目标失配",
    },
    "1e-7 (grav) or 5 (mag)": {
        "fr": "1e-7 (grav) ou 5 (mag)", "es": "1e-7 (grav) o 5 (mag)",
        "pt": "1e-7 (grav) ou 5 (mag)", "pt_BR": "1e-7 (grav) ou 5 (mag)", "zh": "1e-7（重力）或5（磁力）",
    },
    "Joint Inversion Parameters": {
        "fr": "Paramètres d'inversion conjointe",
        "es": "Parámetros de inversión conjunta",
        "pt": "Parâmetros de inversão conjunta",
        "pt_BR": "Parâmetros de inversão conjunta",
        "zh": "联合反演参数",
    },
    "Grav weight": {
        "fr": "Poids Grav", "es": "Peso Grav",
        "pt": "Peso Grav", "pt_BR": "Peso Grav", "zh": "重力权重",
    },
    "Mag weight": {
        "fr": "Poids Mag", "es": "Peso Mag",
        "pt": "Peso Mag", "pt_BR": "Peso Mag", "zh": "磁力权重",
    },
    "Select directory to save tomofast files": {
        "fr": "Sélectionner le répertoire pour sauvegarder les fichiers tomofast",
        "es": "Seleccionar directorio para guardar archivos tomofast",
        "pt": "Selecionar diretório para salvar arquivos tomofast",
        "pt_BR": "Selecionar diretório para salvar arquivos tomofast",
        "zh": "选择保存tomofast文件的目录",
    },
    "Save Files": {
        "fr": "Enregistrer fichiers", "es": "Guardar archivos",
        "pt": "Salvar arquivos", "pt_BR": "Salvar arquivos", "zh": "保存文件",
    },
    "Output Directory": {
        "fr": "Répertoire de sortie", "es": "Directorio de salida",
        "pt": "Diretório de saída", "pt_BR": "Diretório de saída", "zh": "输出目录",
    },
    "Run Inversion": {
        "fr": "Lancer l'inversion", "es": "Ejecutar inversión",
        "pt": "Executar inversão", "pt_BR": "Executar inversão", "zh": "运行反演",
    },
    "Path to tomofast": {
        "fr": "Chemin vers tomofast", "es": "Ruta a tomofast",
        "pt": "Caminho para tomofast", "pt_BR": "Caminho para tomofast", "zh": "tomofast路径",
    },
    "Path to parfile": {
        "fr": "Chemin vers le fichier de paramètres",
        "es": "Ruta al archivo de parámetros",
        "pt": "Caminho para o arquivo de parâmetros",
        "pt_BR": "Caminho para o arquivo de parâmetros",
        "zh": "参数文件路径",
    },
    "Number of processors": {
        "fr": "Nombre de processeurs", "es": "Número de procesadores",
        "pt": "Número de processadores", "pt_BR": "Número de processadores", "zh": "处理器数量",
    },
    "WSL Distro": {
        "fr": "Distribution WSL", "es": "Distribución WSL",
        "pt": "Distribuição WSL", "pt_BR": "Distribuição WSL", "zh": "WSL发行版",
    },
    "Path to mpirun/mpiexec": {
        "fr": "Chemin vers mpirun/mpiexec",
        "es": "Ruta a mpirun/mpiexec",
        "pt": "Caminho para mpirun/mpiexec",
        "pt_BR": "Caminho para mpirun/mpiexec",
        "zh": "mpirun/mpiexec路径",
    },
    "Visualise": {
        "fr": "Visualiser", "es": "Visualizar",
        "pt": "Visualizar", "pt_BR": "Visualizar", "zh": "可视化",
    },
    "Download Plugin Manual": {
        "fr": "Télécharger le manuel du plugin",
        "es": "Descargar manual del plugin",
        "pt": "Baixar manual do plugin",
        "pt_BR": "Baixar manual do plugin",
        "zh": "下载插件手册",
    },
    "Download Tomofast-x  Manual": {
        "fr": "Télécharger le manuel Tomofast-x",
        "es": "Descargar manual Tomofast-x",
        "pt": "Baixar manual Tomofast-x",
        "pt_BR": "Baixar manual Tomofast-x",
        "zh": "下载Tomofast-x手册",
    },
    "Export": {
        "fr": "Exporter", "es": "Exportar",
        "pt": "Exportar", "pt_BR": "Exportar", "zh": "导出",
    },
    "Windows Native": {
        "fr": "Windows natif", "es": "Windows nativo",
        "pt": "Windows nativo", "pt_BR": "Windows nativo", "zh": "Windows原生",
    },
    "Windows WSL": {
        "fr": "Windows WSL", "es": "Windows WSL",
        "pt": "Windows WSL", "pt_BR": "Windows WSL", "zh": "Windows WSL",
    },
    "Path to setvars.bat": {
        "fr": "Chemin vers setvars.bat",
        "es": "Ruta a setvars.bat",
        "pt": "Caminho para setvars.bat",
        "pt_BR": "Caminho para setvars.bat",
        "zh": "setvars.bat路径",
    },
    "Download Plugin Cheat Sheet": {
        "fr": "Télécharger la fiche de référence du plugin",
        "es": "Descargar hoja de referencia del plugin",
        "pt": "Baixar guia rápido do plugin",
        "pt_BR": "Baixar guia rápido do plugin",
        "zh": "下载插件速查表",
    },
    "Grav Depth Weighting": {
        "fr": "Pondération en profondeur Grav",
        "es": "Ponderación en profundidad Grav",
        "pt": "Ponderação em profundidade Grav",
        "pt_BR": "Ponderação em profundidade Grav",
        "zh": "重力深度加权",
    },
    "Enable Depth Weighting": {
        "fr": "Activer la pondération en profondeur",
        "es": "Activar ponderación en profundidad",
        "pt": "Ativar ponderação em profundidade",
        "pt_BR": "Ativar ponderação em profundidade",
        "zh": "启用深度加权",
    },
    "Power": {
        "fr": "Puissance", "es": "Potencia",
        "pt": "Potência", "pt_BR": "Potência", "zh": "幂次",
    },
    "Distance-based": {
        "fr": "Basé sur la distance", "es": "Basado en distancia",
        "pt": "Baseado em distância", "pt_BR": "Baseado em distância", "zh": "基于距离",
    },
    "Depth-based": {
        "fr": "Basé sur la profondeur", "es": "Basado en profundidad",
        "pt": "Baseado em profundidade", "pt_BR": "Baseado em profundidade", "zh": "基于深度",
    },
    "Mag  Depth Weighting": {
        "fr": "Pondération en profondeur Mag",
        "es": "Ponderación en profundidad Mag",
        "pt": "Ponderação em profundidade Mag",
        "pt_BR": "Ponderação em profundidade Mag",
        "zh": "磁力深度加权",
    },
}

LANG_NAMES = {
    "fr": "fr",
    "es": "es",
    "pt": "pt",
    "pt_BR": "pt_BR",
    "zh": "zh",
}


def escape_xml(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def make_ts(lang_code):
    messages = []
    for line_num, (source, translations) in enumerate(TRANSLATIONS.items(), start=1):
        translation = translations.get(lang_code, source)
        messages.append(
            f'    <message>\n'
            f'        <location filename="{UI_FILE}" line="{line_num}"/>\n'
            f'        <source>{escape_xml(source)}</source>\n'
            f'        <translation>{escape_xml(translation)}</translation>\n'
            f'    </message>'
        )
    body = "\n".join(messages)
    return (
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<!DOCTYPE TS><TS version="2.0" language="{lang_code}" sourcelanguage="en">\n'
        f'<context>\n'
        f'    <name>{CONTEXT}</name>\n'
        f'{body}\n'
        f'</context>\n'
        f'</TS>\n'
    )


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for lang_code in LANG_NAMES:
        content = make_ts(lang_code)
        filename = os.path.join(script_dir, f"Tomofast_x_{lang_code}.ts")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Written: {filename}")

    print("\nTo compile .ts files to .qm, run:")
    print("  lrelease *.ts")
    print("Or from QGIS Python console:")
    print("  import subprocess; subprocess.run(['lrelease', 'path/to/i18n/*.ts'])")
