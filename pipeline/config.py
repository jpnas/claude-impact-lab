import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DATA_ROOT = Path(os.getenv("DATA_ROOT", "../claude_impact_lab_compstat_rio"))
DADOS = DATA_ROOT / "dados"
RELINTS = DATA_ROOT / "relints"
SHAPEFILE = DATA_ROOT / "sh_area_forca" / "areas_forca_municipal"
OUTROS = DADOS / "outros dados"

OCORRENCIAS_CSV = DADOS / "df_ocorrencias_tratado - Extração 1 .csv"
DISK_DENUNCIA_CSV = DADOS / "disk_denuncia.csv"
FATORES_CSV = DADOS / "fatores_urbanos.csv"
CAMERAS_CSV = DADOS / "cameras_areas_fm.csv"
DOMINIO_CSV = OUTROS / "dominio_territorial - Extração 1.csv"
PSR_XLSX = OUTROS / "CPSR_2020_2022_2024.xlsx"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

RAIO_METROS = 100
DD_CLASSES_CRIMINAIS = {
    "CRIMES CONTRA O PATRIMÔNIO",
    "SUBSTÂNCIAS ENTORPECENTES",
    "ARMAS DE FOGO E ARTEFATOS EXPLOSIVOS",
}
DD_TOP_N = 40
JANELA_MESES = 12
