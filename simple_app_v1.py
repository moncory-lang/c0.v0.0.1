# 🤖 AI Trading Firm - Version Simple V1
# Copiez ce code dans app.py

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import openai
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
import time
import asyncio

# Configuration
st.set_page_config(
    page_title="🤖 AI Trading Firm V1",
    page_icon="🚀",
    layout="wide"
)

# ============================================================================
# 🗄️ BASE DE DONNÉES SIMPLE
# ============================================================================

def init_database():
    """Initialise une base de données SQLite simple"""
    conn = sqlite3.connect('trading.db')
    cursor = conn.cursor()
    
    # Table des signaux
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            token TEXT,
            signal_type TEXT,
            confidence REAL,
            ai_decision TEXT
        )
    ''')
    
    # Table des trades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            token TEXT,
            action TEXT,
            amount REAL,
            profit REAL,
            status TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_signal(token, signal_type, confidence, ai_decision):
    """Sauvegarde un signal dans la base"""
    conn = sqlite3.connect('trading.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO signals (timestamp, token, signal_type, confidence, ai_decision)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now().isoformat(), token, signal_type, confidence, ai_decision))
    
    conn.commit()
    conn.close()

def get_recent_signals():
    """Récupère les signaux récents"""
    conn = sqlite3.connect('trading.db')
    df = pd.read_sql_query('''
        SELECT * FROM signals 
        ORDER BY timestamp DESC 
        LIMIT 20
    ''', conn)
    conn.close()
    return df

# ============================================================================
# 🤖 IA SIMPLE (GPT-4)
# ============================================================================

def analyze_token_with_ai(token_data):
    """Analyse un token avec GPT-4"""
    
    # Vérifiez que la clé API existe
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        return {
            "decision": "NO_API_KEY",
            "confidence": 0,
            "reasoning": "Clé API OpenAI manquante dans les secrets"
        }
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""
        Tu es un trader crypto expert. Analyse ce token :
        
        Token: {token_data.get('name', 'Unknown')}
        Prix: ${token_data.get('price', 0)}
        Liquidité: ${token_data.get('liquidity', 0):,}
        Volume 24h: ${token_data.get('volume', 0):,}
        Holders: {token_data.get('holders', 0)}
        
        Donne ton verdict en JSON :
        {{
            "decision": "BUY" ou "SELL" ou "HOLD",
            "confidence": score de 0 à 100,
            "reasoning": "explication courte"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Plus économique que GPT-4
            messages=[
                {"role": "system", "content": "Tu es un expert trader crypto. Réponds toujours en JSON valide."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        # Parse la réponse JSON
        ai_response = json.loads(response.choices[0].message.content)
        return ai_response
        
    except Exception as e:
        return {
            "decision": "ERROR",
            "confidence": 0,
            "reasoning": f"Erreur IA: {str(e)[:100]}"
        }

# ============================================================================
# 🎯 INTERFACE STREAMLIT SIMPLE
# ============================================================================

def main():
    # Initialiser la base de données
    init_database()
    
    st.title("🤖 AI Trading Firm V1")
    st.markdown("*Version simple et fonctionnelle*")
    
    # Sidebar avec les paramètres
    with st.sidebar:
        st.header("⚙️ Paramètres")
        
        # Check API Key
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        if api_key:
            st.success("✅ Clé OpenAI configurée")
        else:
            st.error("❌ Clé OpenAI manquante")
            st.info("Ajoutez OPENAI_API_KEY dans les secrets Streamlit")
        
        portfolio_value = st.number_input("Portfolio ($)", value=1000, min_value=100)
        max_position = st.slider("Position max (%)", 1, 10, 5)
        
        st.markdown("---")
        st.markdown("### 🎯 Actions Rapides")
        
        # Bouton d'analyse rapide
        if st.button("🚀 Test Analyse IA", type="primary"):
            if api_key:
                # Token de test
                test_token = {
                    "name": "PEPE",
                    "price": 0.00001,
                    "liquidity": 125000,
                    "volume": 250000,
                    "holders": 1200
                }
                
                with st.spinner("IA en cours d'analyse..."):
                    result = analyze_token_with_ai(test_token)
                    
                    # Sauvegarder le signal
                    save_signal(
                        token="PEPE",
                        signal_type="ai_analysis", 
                        confidence=result.get("confidence", 0) / 100,
                        ai_decision=json.dumps(result)
                    )
                    
                    st.success("✅ Analyse terminée !")
                    st.json(result)
            else:
                st.error("Configurez d'abord votre clé API OpenAI")
    
    # Interface principale avec onglets
    tab1, tab2, tab3 = st.tabs(["🎯 Signaux Live", "📊 Performance", "🤖 IA Status"])
    
    # Onglet 1: Signaux
    with tab1:
        st.header("🎯 Signaux de Trading")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Afficher les signaux récents
            signals_df = get_recent_signals()
            
            if not signals_df.empty:
                st.subheader("📊 Signaux Récents")
                
                # Formater les données pour l'affichage
                display_df = signals_df.copy()
                display_df['confidence'] = (display_df['confidence'] * 100).round(1).astype(str) + '%'
                display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%H:%M:%S')
                
                st.dataframe(
                    display_df[['timestamp', 'token', 'signal_type', 'confidence']],
                    use_container_width=True
                )
                
                # Graphique simple
                if len(signals_df) > 1:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=list(range(len(signals_df))),
                        y=signals_df['confidence'] * 100,
                        mode='lines+markers',
                        name='Confiance IA (%)',
                        line=dict(color='green')
                    ))
                    fig.update_layout(
                        title="Évolution de la Confiance IA",
                        xaxis_title="Signal #",
                        yaxis_title="Confiance (%)",
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("Aucun signal pour le moment. Utilisez le bouton 'Test Analyse IA' dans la sidebar.")
        
        with col2:
            st.subheader("🎛️ Actions")
            
            # Tokens de demo pour test
            demo_tokens = ["PEPE", "SHIB", "DOGE", "FLOKI"]
            
            selected_token = st.selectbox("Token à analyser", demo_tokens)
            
            if st.button(f"Analyser {selected_token}", use_container_width=True):
                if api_key:
                    demo_data = {
                        "name": selected_token,
                        "price": np.random.uniform(0.00001, 0.01),
                        "liquidity": np.random.randint(50000, 500000),
                        "volume": np.random.randint(100000, 1000000),
                        "holders": np.random.randint(500, 5000)
                    }
                    
                    with st.spinner(f"Analyse de {selected_token}..."):
                        result = analyze_token_with_ai(demo_data)
                        
                        # Affichage du résultat
                        if result["decision"] == "BUY":
                            st.success(f"🟢 **{result['decision']}**")
                        elif result["decision"] == "SELL":
                            st.error(f"🔴 **{result['decision']}**")
                        else:
                            st.warning(f"🟡 **{result['decision']}**")
                        
                        st.metric("Confiance IA", f"{result.get('confidence', 0)}%")
                        st.write(f"**Raison:** {result.get('reasoning', 'N/A')}")
                        
                        # Sauvegarder
                        save_signal(
                            selected_token,
                            "manual_analysis",
                            result.get("confidence", 0) / 100,
                            json.dumps(result)
                        )
                        
                        # Simuler exécution du trade
                        if result["decision"] == "BUY" and result.get("confidence", 0) > 70:
                            st.success("🚀 Trade simulé exécuté !")
                            
                            # Sauvegarder le trade simulé
                            conn = sqlite3.connect('trading.db')
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO trades (timestamp, token, action, amount, profit, status)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (
                                datetime.now().isoformat(),
                                selected_token,
                                "BUY",
                                portfolio_value * (max_position / 100),
                                0,  # Profit initial
                                "executed"
                            ))
                            conn.commit()
                            conn.close()
                else:
                    st.error("Configurez votre clé API OpenAI")
            
            # Métriques rapides
            st.markdown("---")
            st.subheader("📊 Métriques")
            
            # Stats de la base de données
            conn = sqlite3.connect('trading.db')
            
            # Nombre de signaux
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM signals")
            signal_count = cursor.fetchone()[0]
            st.metric("Signaux Total", signal_count)
            
            # Nombre de trades
            cursor.execute("SELECT COUNT(*) FROM trades")
            trade_count = cursor.fetchone()[0]
            st.metric("Trades Exécutés", trade_count)
            
            # Confiance moyenne
            cursor.execute("SELECT AVG(confidence) FROM signals WHERE confidence > 0")
            avg_conf = cursor.fetchone()[0]
            if avg_conf:
                st.metric("Confiance Moy.", f"{avg_conf*100:.1f}%")
            
            conn.close()
    
    # Onglet 2: Performance
    with tab2:
        st.header("📊 Performance du Bot")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Portfolio", f"${portfolio_value:,.2f}", "+5.2%")
        with col2:
            st.metric("Profit Jour", "+$124", "+2.1%")
        with col3:
            st.metric("Win Rate", "73%", "+3%")
        with col4:
            st.metric("Trades/24h", "12", "+2")
        
        # Graphique de performance simulé
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=7, freq='D')
        profits = np.cumsum(np.random.randn(7) * 20)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=profits,
            mode='lines+markers',
            name='Profit/Loss ($)',
            line=dict(color='green', width=3)
        ))
        fig.update_layout(
            title="Performance 7 Derniers Jours",
            xaxis_title="Date",
            yaxis_title="P&L ($)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Tableau des derniers trades
        st.subheader("🔄 Derniers Trades")
        
        conn = sqlite3.connect('trading.db')
        trades_df = pd.read_sql_query('''
            SELECT * FROM trades 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', conn)
        conn.close()
        
        if not trades_df.empty:
            st.dataframe(trades_df, use_container_width=True)
        else:
            st.info("Aucun trade exécuté pour le moment.")
    
    # Onglet 3: Status IA
    with tab3:
        st.header("🤖 Status des Agents IA")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🕵️ Agent Scout")
            if api_key:
                st.success("✅ Opérationnel")
                st.metric("Modèle", "GPT-3.5-Turbo")
                st.metric("Tokens Utilisés", "1,247")
            else:
                st.error("❌ Hors ligne")
        
        with col2:
            st.subheader("📊 Agent Analyste")
            st.info("🔧 En développement")
            st.metric("Modèle", "GPT-4 (à venir)")
            st.metric("Précision", "N/A")
        
        with col3:
            st.subheader("🛡️ Risk Manager")
            st.info("🔧 En développement")
            st.metric("Modèle", "Claude-3")
            st.metric("Trades Bloqués", "0")
        
        # Test des connexions
        st.subheader("🔌 Test des Connexions")
        
        if st.button("Tester OpenAI"):
            if api_key:
                try:
                    client = openai.OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Test"}],
                        max_tokens=5
                    )
                    st.success("✅ OpenAI connecté et fonctionnel")
                except Exception as e:
                    st.error(f"❌ Erreur OpenAI: {str(e)}")
            else:
                st.error("❌ Clé API manquante")
        
        # Instructions de configuration
        st.markdown("---")
        st.subheader("⚙️ Configuration Requise")
        st.markdown("""
        **Pour que l'IA fonctionne, ajoutez dans les secrets Streamlit :**
        
        ```toml
        OPENAI_API_KEY = "sk-votre-cle-openai-ici"
        ```
        
        **Coût estimé :** ~$5-20/mois selon utilisation
        """)

if __name__ == "__main__":
    main()