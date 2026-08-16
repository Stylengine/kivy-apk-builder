import sys
import os

# --- FORCE NATIVE WINDOW ENGINE PARAMETERS IMMEDIATELY ---
from kivy.config import Config
Config.set('graphics', 'width', '420')
Config.set('graphics', 'height', '720')
Config.set('graphics', 'resizable', '0')

from kivy.core.window import Window
Window.size = (420, 720)
# --------------------------------------------------------

import yfinance as ticker_engine
import pandas as pd
import numpy as np
from datetime import datetime
import time
import threading

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

class LoginScreen(Screen):
    """Secures access points behind local gate check validation loops."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15)
        
        lbl = Label(text="🔒 Security Gateway", font_size='22sp', bold=True, size_hint_y=None, height=50)
        sub = Label(text="Enter passcode to unlock risk terminal:", font_size='14sp', color=(0.6, 0.6, 0.7, 1), size_hint_y=None, height=30)
        
        self.pass_input = TextInput(password=True, multiline=False, size_hint_y=None, height=45, halign='center', font_size='18sp')
        self.pass_input.bind(on_text_validate=self.verify_passcode)
        
        btn = Button(text="Unlock Dashboard", background_color=(0.23, 0.51, 0.96, 1), font_size='16sp', bold=True, size_hint_y=None, height=50)
        btn.bind(on_press=self.verify_passcode)
        
        self.err_lbl = Label(text="", color=(0.95, 0.24, 0.37, 1), font_size='14sp', size_hint_y=None, height=30)
        
        layout.add_widget(lbl)
        layout.add_widget(sub)
        layout.add_widget(self.pass_input)
        layout.add_widget(btn)
        layout.add_widget(self.err_lbl)
        self.add_widget(layout)

    def verify_passcode(self, instance):
        if self.pass_input.text == "MySecretPassword123":
            self.manager.current = 'dashboard'
        else:
            self.err_lbl.text = "❌ Invalid security passcode credential."

class DashboardScreen(Screen):
    """Clean Dashboard featuring User Inputs, Structural Targets, and Volatility-Based ETA Projections."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.my_portfolio = []
        self.main_layout = BoxLayout(orientation='vertical', padding=15, spacing=12)
        
        # 1. Macro Indices Real-time Data Bar Header
        self.macro_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=55, spacing=10)
        self.nifty_lbl = Label(text="Nifty 50:\n...", font_size='13sp', bold=True, halign='center')
        self.vix_lbl = Label(text="India VIX:\n...", font_size='13sp', bold=True, halign='center')
        self.macro_box.add_widget(self.nifty_lbl)
        self.macro_box.add_widget(self.vix_lbl)
        self.main_layout.add_widget(self.macro_box)
        
        # 2. Dynamic Ticker Input Toolbar Interface
        input_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=8)
        self.ticker_input = TextInput(
            hint_text="Enter NSE Symbol (e.g. RELIANCE, SBIN)", 
            multiline=False, font_size='14sp', halign='center'
        )
        self.ticker_input.bind(on_text_validate=self.add_custom_stock_node)
        
        self.add_btn = Button(text="➕ Add Stock", font_size='13sp', bold=True, background_color=(0.23, 0.51, 0.96, 1), size_hint_x=None, width=110)
        self.add_btn.bind(on_press=self.add_custom_stock_node)
        
        input_box.add_widget(self.ticker_input)
        input_box.add_widget(self.add_btn)
        self.main_layout.add_widget(input_box)
        
        # 3. Dynamic Execution Trigger Command Bar
        self.run_btn = Button(text="🔄 Sync Metrics & Volatility ETAs", font_size='14sp', bold=True, background_color=(0.09, 0.64, 0.29, 1), size_hint_y=None, height=45)
        self.run_btn.bind(on_press=self.run_market_engine_scan)
        self.main_layout.add_widget(self.run_btn)
        
        # 4. Scrollable Data Grid Matrix Header Nodes
        header_grid = GridLayout(cols=6, size_hint_y=None, height=30)
        headers = [("ASSET", 1.0), ("CMP", 1.0), ("BUY TGT\n(DAYS)", 1.2), ("SELL TGT\n(DAYS)", 1.2), ("WEIGHT", 0.9), ("DEL", 0.5)]
        for h, weight in headers:
            header_grid.add_widget(Label(text=h, bold=True, font_size='10sp', halign='center', color=(0.7, 0.7, 0.8, 1), size_hint_x=weight))
        self.main_layout.add_widget(header_grid)
        
        # 5. Core Content Scroll Canvas Framework
        self.scroll_view = ScrollView()
        self.data_grid = GridLayout(cols=6, size_hint_y=None, spacing=4)
        self.data_grid.bind(minimum_height=self.data_grid.setter('height'))
        self.scroll_view.add_widget(self.data_grid)
        self.main_layout.add_widget(self.scroll_view)
        
        self.add_widget(self.main_layout)
        
        # --- FIX: Populate visual warning text cleanly first instead of crashing ---
        Clock.schedule_once(self._set_initial_empty_state, 0.1)

    def _set_initial_empty_state(self, dt):
        """Pre-populates an empty text block so Kivy doesn't break."""
        self.data_grid.clear_widgets()
        self.data_grid.add_widget(Label(text="No Stocks Tracked", font_size='12sp', color=(0.5, 0.5, 0.6, 1), size_hint_x=5, size_hint_y=None, height=40))

    def add_custom_stock_node(self, instance):
        symbol = self.ticker_input.text.strip().upper()
        if symbol and symbol not in self.my_portfolio:
            self.my_portfolio.append(symbol)
            self.ticker_input.text = "" 
            self.run_market_engine_scan(None) 

    def remove_stock_node(self, ticker_to_remove):
        if ticker_to_remove in self.my_portfolio:
            self.my_portfolio.remove(ticker_to_remove)
            self.run_market_engine_scan(None)

    def run_market_engine_scan(self, instance):
        self.run_btn.text = "⚡ Syncing Market Engine..."
        self.run_btn.disabled = True
        threading.Thread(target=self._async_market_worker, daemon=True).start()

    def _async_market_worker(self):
        try:
            nifty_df = ticker_engine.Ticker("^NSEI").history(period="5d")
            vix_df = ticker_engine.Ticker("^INDIAVIX").history(period="5d")
            nifty_spot = round(nifty_df['Close'].iloc[-1], 1) if not nifty_df.empty else 24000.0
            vix_level = round(vix_df['Close'].iloc[-1], 1) if not vix_df.empty else 14.5
            
            macro_data = {
                "nifty": f"📊 Nifty 50\n{nifty_spot}",
                "vix": f"🛡️ India VIX\n{vix_level} ({'RISK' if vix_level > 22.0 else 'STABLE'})"
            }

            processed = []
            raw_scores = []
            
            for ticker in self.my_portfolio:
                ns_ticker = ticker + '.NS' if not ticker.endswith('.NS') and not ticker.endswith('.BO') else ticker
                stock = ticker_engine.Ticker(ns_ticker)
                df = stock.history(period="6mo")
                if df.empty or len(df) < 20: 
                    continue
                
                cmp = stock.info.get("currentPrice") or stock.info.get("regularMarketPrice")
                if not cmp: 
                    cmp = round(df['Close'].iloc[-1], 1)
                
                recent = df.tail(20).copy()
                floor = recent['Low'].min()
                ceiling = recent['High'].max()
                
                buy_target = round(floor * 1.01, 1)    
                sell_target = round(ceiling * 0.99, 1) 
                stop_loss = round(floor * 0.97, 1)     
                
                high_low = recent['High'] - recent['Low']
                high_pc = (recent['High'] - recent['Close'].shift(1)).abs()
                low_pc = (recent['Low'] - recent['Close'].shift(1)).abs()
                
                true_range = pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1)
                atr = true_range.mean()
                if atr <= 0: 
                    atr = cmp * 0.01  
                
                buy_distance = cmp - buy_target
                sell_distance = sell_target - cmp
                
                buy_eta = f"{max(1, round(buy_distance / atr))}" if buy_distance > 0 else "Triggered"
                sell_eta = f"{max(1, round(sell_distance / atr))}" if sell_distance > 0 else "Triggered"
                
                score = max(0.0, min(1.0, (ceiling - cmp) / (ceiling - floor))) if ceiling > floor else 0.5
                
                raw_scores.append(score)
                processed.append({
                    "ticker": ticker, "price": cmp, 
                    "buy": buy_target, "buy_eta": buy_eta,
                    "sell": sell_target, "sell_eta": sell_eta,
                    "stop": stop_loss, "score": score
                })
                time.sleep(0.02)

            total_score = sum(raw_scores) if sum(raw_scores) > 0 else 1
            equity_multiplier = 0.8 if vix_level > 22.0 else 1.0
            
            payload = {
                "macro": macro_data,
                "processed": processed,
                "total_score": total_score,
                "equity_multiplier": equity_multiplier
            }
            Clock.schedule_once(lambda dt: self._update_ui_graphics(payload))
            
        except Exception as err:
            print(f"Error handling market data background worker: {err}")
            Clock.schedule_once(lambda dt: self._reset_sync_button())

    def _update_ui_graphics(self, payload):
        self.nifty_lbl.text = payload["macro"]["nifty"]
        self.vix_lbl.text = payload["macro"]["vix"]
