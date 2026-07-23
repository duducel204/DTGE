# -*- coding: utf-8 -*-
"""
test_dtge_logger.py — Testes unitários para sistema de logging centralizado
"""

import os
import json
import tempfile
import shutil
from pathlib import Path

import dtge_logger

def setup_test_env():
    """Cria ambiente temporário para testes."""
    test_dir = tempfile.mkdtemp(prefix="dtge_test_")
    os.chdir(test_dir)
    return test_dir

def cleanup_test_env(test_dir):
    """Limpa ambiente de teste."""
    os.chdir("/")
    shutil.rmtree(test_dir, ignore_errors=True)

def test_registrar_log():
    """Test 1: Registrar evento no log."""
    print("\n[TEST 1] Registrar evento no log...")
    test_dir = setup_test_env()
    
    try:
        resultado = dtge_logger.registrar_log(
            agente="TestAgent",
            tipo_evento="DECIDIR",
            mensagem="Teste de registro",
            detalhes={"teste": True},
            autorizado_por="TEST_USER",
        )
        
        assert resultado["seq"] == 1, "Primeira sequência deve ser 1"
        assert "hash" in resultado, "Resultado deve conter hash"
        assert os.path.exists(dtge_logger.MASTER_LOG), "Log file deve existir"
        
        print(f"✓ Evento registrado: seq={resultado['seq']}, hash={resultado['hash'][:8]}...")
    finally:
        cleanup_test_env(test_dir)

def test_registrar_hash_artefato():
    """Test 2: Registrar hash de artefato."""
    print("\n[TEST 2] Registrar hash de artefato...")
    test_dir = setup_test_env()
    
    try:
        # Cria arquivo de teste
        arquivo_teste = os.path.join(test_dir, "teste.txt")
        with open(arquivo_teste, "w") as f:
            f.write("Conteúdo de teste")
        
        resultado = dtge_logger.registrar_hash_artefato(
            caminho_artefato=arquivo_teste,
            tipo_artefato="teste",
            autorizado_por="TEST_USER",
        )
        
        assert "hash_sha256" in resultado, "Resultado deve conter hash"
        assert len(resultado["hash_sha256"]) == 64, "Hash SHA256 deve ter 64 caracteres"
        assert os.path.exists(dtge_logger.HASHES_REGISTRY), "Hashes registry deve existir"
        
        print(f"✓ Hash registrado: {resultado['hash_sha256'][:8]}...")
    finally:
        cleanup_test_env(test_dir)

def test_verificar_integridade():
    """Test 3: Verificar integridade de artefato."""
    print("\n[TEST 3] Verificar integridade...")
    test_dir = setup_test_env()
    
    try:
        # Cria arquivo
        arquivo_teste = os.path.join(test_dir, "teste.txt")
        with open(arquivo_teste, "w") as f:
            f.write("Conteúdo original")
        
        # Calcula hash
        resultado_hash = dtge_logger.registrar_hash_artefato(
            caminho_artefato=arquivo_teste,
            tipo_artefato="teste",
            autorizado_por="TEST_USER",
        )
        
        hash_esperado = resultado_hash["hash_sha256"]
        
        # Verifica integridade
        integro = dtge_logger.verificar_integridade_artefato(
            caminho_artefato=arquivo_teste,
            hash_esperado=hash_esperado,
        )
        
        assert integro, "Arquivo não alterado deve passar na verificação"
        print("✓ Arquivo íntegro (verificação OK)")
        
        # Altera arquivo
        with open(arquivo_teste, "w") as f:
            f.write("Conteúdo alterado")
        
        # Verifica novamente (deve falhar)
        integro_alterado = dtge_logger.verificar_integridade_artefato(
            caminho_artefato=arquivo_teste,
            hash_esperado=hash_esperado,
        )
        
        assert not integro_alterado, "Arquivo alterado deve falhar na verificação"
        print("✓ Arquivo alterado foi detectado (verificação OK)")
    finally:
        cleanup_test_env(test_dir)

def test_listar_logs_agente():
    """Test 4: Listar logs de agente específico."""
    print("\n[TEST 4] Listar logs por agente...")
    test_dir = setup_test_env()
    
    try:
        # Registra alguns eventos
        for i in range(3):
            dtge_logger.registrar_log(
                agente="Agent1",
                tipo_evento="DECIDIR",
                mensagem=f"Evento {i}",
            )
        
        for i in range(2):
            dtge_logger.registrar_log(
                agente="Agent2",
                tipo_evento="SEGUIR",
                mensagem=f"Evento {i}",
            )
        
        # Lista logs de Agent1
        logs_agent1 = dtge_logger.listar_logs_agente("Agent1")
        assert len(logs_agent1) == 3, "Agent1 deve ter 3 logs"
        print(f"✓ Agent1 tem {len(logs_agent1)} logs")
        
        # Lista logs de Agent2
        logs_agent2 = dtge_logger.listar_logs_agente("Agent2")
        assert len(logs_agent2) == 2, "Agent2 deve ter 2 logs"
        print(f"✓ Agent2 tem {len(logs_agent2)} logs")
    finally:
        cleanup_test_env(test_dir)

def test_resumo_sistema():
    """Test 5: Resumo do sistema."""
    print("\n[TEST 5] Resumo do sistema...")
    test_dir = setup_test_env()
    
    try:
        # Registra vários eventos
        dtge_logger.registrar_log("Agent1", "DECIDIR", "Msg 1")
        dtge_logger.registrar_log("Agent1", "SEGUIR", "Msg 2")
        dtge_logger.registrar_log("Agent2", "ALERTA", "Msg 3")
        
        resumo = dtge_logger.resumo_sistema()
        
        assert resumo["total_logs"] == 3, "Deve haver 3 logs"
        assert "Agent1" in resumo["agentes_ativos"], "Agent1 deve estar ativo"
        assert "Agent2" in resumo["agentes_ativos"], "Agent2 deve estar ativo"
        
        print(f"✓ Sistema tem {resumo['total_logs']} logs")
        print(f"✓ Agentes ativos: {', '.join(resumo['agentes_ativos'])}")
        print(f"✓ Tipos de evento: {resumo['tipos_evento']}")
    finally:
        cleanup_test_env(test_dir)

def test_sequencia_incremental():
    """Test 6: Sequência incremental de eventos."""
    print("\n[TEST 6] Sequência incremental...")
    test_dir = setup_test_env()
    
    try:
        resultados = []
        for i in range(5):
            resultado = dtge_logger.registrar_log(
                agente="TestAgent",
                tipo_evento="DECIDIR",
                mensagem=f"Evento {i}",
            )
            resultados.append(resultado["seq"])
        
        assert resultados == [1, 2, 3, 4, 5], "Sequência deve ser incremental"
        print(f"✓ Sequência incremental: {resultados}")
    finally:
        cleanup_test_env(test_dir)

if __name__ == "__main__":
    print("="*50)
    print("SUITE DE TESTES: dtge_logger.py")
    print("="*50)
    
    test_registrar_log()
    test_registrar_hash_artefato()
    test_verificar_integridade()
    test_listar_logs_agente()
    test_resumo_sistema()
    test_sequencia_incremental()
    
    print("\n" + "="*50)
    print("✓ TODOS OS TESTES PASSARAM")
    print("="*50)
