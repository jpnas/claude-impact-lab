from __future__ import annotations
import logging
from datetime import datetime
from supabase import create_client, Client

from pipeline.config import SHAPEFILE, SUPABASE_URL, SUPABASE_SERVICE_KEY
from pipeline.utils.shapefile import load_areas
from pipeline.processadores.ocorrencias import build_ocorrencias_base
from pipeline.processadores.fatores_urbanos import build_fatores_urbanos_base
from pipeline.processadores.cobertura_operacional import build_cobertura_operacional
from pipeline.processadores.contexto_territorial import build_contexto_territorial
from pipeline.processadores.dinamica_criminal import (
    build_dinamica_criminal, enrich_ocorrencias_dd, enrich_fatores_relint
)
from pipeline.processadores.coincidencias import build_coincidencias

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_area_id(sb: Client, nome: str) -> str | None:
    res = sb.table("areas").select("id").eq("nome", nome).execute()
    if res.data:
        return res.data[0]["id"]
    return None


def upsert_dimensao(sb: Client, area_id: str, tipo: str, dados: dict) -> None:
    sb.table("dimensoes_analise").upsert(
        {
            "area_id": area_id,
            "tipo": tipo,
            "dados": dados,
            "referencia_pipeline": datetime.utcnow().isoformat(),
        },
        on_conflict="area_id,tipo",
    ).execute()
    log.info(f"  ✓ {tipo}")


def process_area(sb: Client, area_nome: str, polygon) -> None:
    log.info(f"=== {area_nome} ===")
    area_id = get_area_id(sb, area_nome)
    if not area_id:
        log.warning(f"  área não encontrada no Supabase: {area_nome}")
        return

    # Phase 1: deterministic
    log.info("  Fase 1...")
    try:
        oc_base = build_ocorrencias_base(polygon)
    except Exception as e:
        log.error(f"  ocorrencias failed: {e}")
        oc_base = {
            "total_periodo": 0,
            "variacao_yoy": "N/A",
            "periodo_referencia": "N/A",
            "por_tipo": {},
            "por_hora": {},
            "por_dia_semana": {},
            "hora_critica": None,
            "dia_critico": None,
            "top_logradouros": [],
            "heatmap_points": [],
        }
    try:
        fat_base = build_fatores_urbanos_base(area_nome, polygon)
    except Exception as e:
        log.error(f"  fatores_urbanos failed: {e}")
        fat_base = {"fatores": [], "por_orgao": {}, "fatores_adicionais_relint": []}
    try:
        cob = build_cobertura_operacional(area_nome, polygon)
    except Exception as e:
        log.error(f"  cobertura_operacional failed: {e}")
        cob = {"poligono": {}, "cameras": [], "total_cameras": 0, "pontos_cegos": []}
    try:
        ctx = build_contexto_territorial(polygon)
    except Exception as e:
        log.error(f"  contexto_territorial failed: {e}")
        ctx = {"orcrim_dominante": "N/A", "orcrim_por_tipo": {}, "comunidades_proximas": [], "psr": {}}

    upsert_dimensao(sb, area_id, "cobertura_operacional", cob)
    upsert_dimensao(sb, area_id, "contexto_territorial", ctx)

    # Phase 2: LLM enrichment
    log.info("  Fase 2 (LLM)...")
    try:
        oc_final = enrich_ocorrencias_dd(oc_base, polygon)
    except Exception as e:
        log.error(f"  enrich_ocorrencias_dd failed: {e}")
        oc_final = oc_base
    try:
        fat_final = enrich_fatores_relint(fat_base, area_nome)
    except Exception as e:
        log.error(f"  enrich_fatores_relint failed: {e}")
        fat_final = fat_base
    try:
        din = build_dinamica_criminal(area_nome, polygon, ctx.get("orcrim_dominante", "N/A"))
    except Exception as e:
        log.error(f"  dinamica_criminal failed: {e}")
        din = {"modalidade_predominante": "N/A", "modus_operandi": "", "rotas_de_fuga": [], "pontos_de_receptacao": [], "perfil_suspeitos": "", "orcrim_influencia": "", "narrativa_completa": ""}

    upsert_dimensao(sb, area_id, "ocorrencias", oc_final)
    upsert_dimensao(sb, area_id, "fatores_urbanos", fat_final)
    upsert_dimensao(sb, area_id, "dinamica_criminal", din)

    # Phase 3: LLM synthesis
    log.info("  Fase 3 (síntese)...")
    try:
        coin = build_coincidencias(oc_final, fat_final, cob, din, ctx)
    except Exception as e:
        log.error(f"  coincidencias failed: {e}")
        coin = {"trechos_criticos": [], "recomendacoes": {}}

    upsert_dimensao(sb, area_id, "coincidencias", coin)
    log.info(f"  Área concluída.")


def main():
    areas = load_areas(SHAPEFILE)
    log.info(f"Pipeline iniciado para {len(areas)} áreas")
    try:
        sb = get_supabase()
    except Exception as e:
        log.error(f"Falha ao conectar ao Supabase: {e}")
        return
    # Verify area names match Supabase
    log.info("Verificando correspondência de áreas com Supabase...")
    for nome in areas.keys():
        aid = get_area_id(sb, nome)
        if aid:
            log.info(f"  ✓ {nome[:50]}")
        else:
            log.warning(f"  ✗ NÃO ENCONTRADO: {nome}")

    for nome, polygon in areas.items():
        try:
            process_area(sb, nome, polygon)
        except Exception as e:
            log.error(f"Erro na área {nome}: {e}", exc_info=True)
    log.info("Pipeline concluído.")


if __name__ == "__main__":
    main()
