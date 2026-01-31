"""
Gemini AI 분석용 데이터 포맷 변환 모듈
"""

import json
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GeminiFormatter:
    """Gemini AI에게 전달할 데이터 포맷 생성"""
    
    def __init__(self):
        pass
    
    def format_for_gemini(
        self,
        stocks_data: Dict,
        technical_analysis: Dict,
        exchange_rates: Dict,
        macro_indicators: Dict,
        kimchi_premium: Dict = None
    ) -> Dict:
        """전체 데이터를 Gemini AI 분석용으로 포맷팅"""
        
        formatted_data = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'market_overview': self._format_market_overview(exchange_rates, macro_indicators),
            'stocks': self._format_stocks(stocks_data, technical_analysis),
            'kimchi_premium': kimchi_premium.get('kimchi_premium', {}) if kimchi_premium else {},
            'raw_data': {
                'exchange_rates': exchange_rates,
                'macro_indicators': macro_indicators,
                'kimchi_premium': kimchi_premium
            }
        }
        
        # Gemini 프롬프트 생성
        formatted_data['gemini_prompt'] = self._generate_gemini_prompt(formatted_data)
        
        return formatted_data
    
    def _format_market_overview(self, exchange_rates: Dict, macro_indicators: Dict) -> Dict:
        """시장 개요 포맷"""
        overview = {
            'exchange_rates': {},
            'economic_indicators': {},
            'market_sentiment': 'NEUTRAL'
        }
        
        # 환율 정보
        if exchange_rates.get('exchange_rates'):
            for currency, data in exchange_rates['exchange_rates'].items():
                if data.get('success'):
                    overview['exchange_rates'][currency] = {
                        'current': data.get('current_rate'),
                        'change_percent': data.get('change_percent', 0),
                        'source': data.get('source')
                    }
        
        # 거시경제 지표
        if macro_indicators.get('macro_indicators'):
            for name, data in macro_indicators['macro_indicators'].items():
                if data.get('success'):
                    overview['economic_indicators'][name] = {
                        'value': data.get('current_value'),
                        'change_percent': data.get('change_percent', 0),
                        'date': data.get('current_date')
                    }
        
        return overview
    
    def _format_stocks(self, stocks_data: Dict, technical_analysis: Dict) -> List[Dict]:
        """주식 정보 포맷"""
        formatted_stocks = []
        
        if not stocks_data.get('stocks'):
            return formatted_stocks
        
        for symbol, stock_data in stocks_data['stocks'].items():
            if not stock_data.get('success'):
                continue
            
            # 기술적 분석 결과
            tech_analysis = technical_analysis.get('technical_analysis', {}).get(symbol, {})
            
            formatted_stock = {
                'symbol': symbol,
                'name': stock_data.get('name', symbol),
                'basic_info': {
                    'current_price': stock_data.get('current_price'),
                    'previous_close': stock_data.get('previous_close'),
                    'day_change': self._calculate_change(
                        stock_data.get('current_price'),
                        stock_data.get('previous_close')
                    ),
                    'volume': stock_data.get('volume'),
                    'market_cap': stock_data.get('market_cap'),
                    'pe_ratio': stock_data.get('pe_ratio'),
                    'sector': stock_data.get('sector'),
                    'industry': stock_data.get('industry')
                },
                'technical_indicators': {
                    'rsi': tech_analysis.get('rsi'),
                    'moving_averages': tech_analysis.get('moving_averages', {}),
                    'bollinger_bands': tech_analysis.get('bollinger_bands', {}),
                    'macd': tech_analysis.get('macd', {}),
                    'volatility': tech_analysis.get('volatility'),
                    'support_resistance': tech_analysis.get('support_resistance', {}),
                    'disparity': tech_analysis.get('disparity', {}),
                    'ma_alignment': tech_analysis.get('ma_alignment', {})
                },
                'signals': tech_analysis.get('signals', {}),
                'data_source': stock_data.get('source', 'unknown')
            }
            
            formatted_stocks.append(formatted_stock)
        
        # 신호 강도순으로 정렬
        formatted_stocks.sort(
            key=lambda x: abs(x.get('signals', {}).get('strength', 0)),
            reverse=True
        )
        
        return formatted_stocks
    
    def _calculate_change(self, current: float, previous: float) -> Dict:
        """가격 변동 계산"""
        if not current or not previous:
            return {'amount': 0, 'percent': 0}
        
        change = current - previous
        change_percent = (change / previous) * 100
        
        return {
            'amount': round(change, 2),
            'percent': round(change_percent, 2)
        }
    
    def _generate_gemini_prompt(self, data: Dict) -> str:
        """Gemini AI 분석용 프롬프트 생성"""
        
        prompt = f"""# Persona: 최고의 투자 파트너, "잼스(Jams)"
당신은 세계 최고의 퀀트 분석가이자 자산배분 전략가 "잼스"입니다. 사용자의 자산을 지키는 방패이자, **수익을 극대화하는 창**의 역할을 수행합니다. 

## 🎯 잼스의 핵심 미션
**수익 극대화를 위한 공격적 투자 전략**을 제시하되, 리스크 관리는 철저히 합니다.
- 사용자가 제공하는 [시장 데이터 JSON]을 분석하여, **"오늘 당장 무엇을 해야 하는지"**를 초등학생도 이해할 수 있을 만큼 구체적이고 단호하게 지시합니다.
- **여유자금을 활용한 알파 수익 창출**에 집중하며, 기회를 놓치지 않도록 적극적으로 지시합니다.
- 보수적 투자가 아닌, **공격적이되 전략적인 투자**를 추구합니다.

## 📊 투자 전략 매뉴얼 (Strict Rules)
1. **테크 주식/ETF (균형)**: 20일 이평선 상단 + RSI 70 미만 시 공격적 매수. RSI 75 초과 시 과열로 간주, 추가 매수 중단.
2. **배당 주식/ETF (역추세)**: 주가 하락 시 배당수익률 상승을 기회로 삼아 매수 강도 높임.
3. **채권 ETF (역추세)**: VIX 지수 급등(20 이상) 시 안전자산 비중 확대 지시.
4. **암호화폐 (순수 추세 + 김치 프리미엄)**:
   - MA20 > MA50 정배열 구간에서만 매수. 역배열 진입 시 즉시 "매수 중단" 및 "관망" 지시.
   - **김치 프리미엄 +5% 이상**: 국내(업비트) 과열. 해외 대비 비싸므로 신규 매수 자제.
   - **김치 프리미엄 -5% 이하**: 국내(업비트) 저평가. 해외 대비 저렴하므로 적극 매수.
   - **김치 프리미엄 -2~+2%**: 정상 범위. 기술적 분석에 따라 매매.
5. **금(Gold) ETF**: VIX 상승 및 KRW 약세 시 헤지 수단으로 추천.
6. **환전 전략**: 환율 1,350원 이하 "적극 환전", 1,400원 이상 "필요량만 환전". 낮 시간(토스 환전 우대 시간) 활용 강조.

## ✍️ 코칭 리포트 작성 형식
### 1. 오늘의 한 줄 요약 (Market Mood)
- 현재 시장을 [공격 / 방어 / 관망] 중 어떤 모드로 임해야 하는지 한 줄로 정의.

### 2. 💰 자금 흐름 및 환전 지시 (Money Move)
- "현재 환율이 [수치]로 [높음/낮음] 상태입니다. 오늘 낮에 [금액]만큼 달러로 환전해두세요."
- "만기 된 발행어음 [금액]은 현재 [종목명]이 저평가 상태이니 여기에 집중 투자하세요."

### 3. 🚀 계좌별 액션 플랜 (Specific Action)
- **ISA 계좌 (국내/해외ETF)**: "TIGER 미국나스닥100은 추세가 좋으니 오늘 2만원 추가 매수하세요."
- **토스증권 (해외주식)**: "NVDA가 과열권입니다. 신규 매수는 쉬고 보유 달러는 현금으로 유지하세요."
- **연금/IRP 계좌**: "시장 변동성이 크니 국채 ETF 비중을 계획보다 5% 더 늘리세요."
- **업비트 (코인)**: "비트코인이 정배열을 유지 중입니다. 주 1회 정기 매수 외에 여유자금의 10%를 오늘 추가 진입하세요."

### 4. ⚠️ 리스크 알림 & 멘탈 케어
- 현재 가장 주의해야 할 지표(VIX, 환율 등)를 언급하며 조심해야 할 부분 경고.

## ❗ 분석 원칙
- "노력해보세요", "생각됩니다" 같은 모호한 표현 금지. 
- "~하세요", "~는 쉬어가세요", "지금이 기회입니다" 등 **확신에 찬 어조** 사용.
- 사용자의 DCA 종목은 기본으로 깔고 가되, **'여유자금'을 활용한 알파 수익**에 집중할 것.

---

# 주식 시장 분석 리포트 ({data['analysis_date']})

## 1. 거시경제 및 시장 환경 분석

### 📊 환율 정보
"""
        
        # 환율 정보 추가
        exchange_rates = data['market_overview']['exchange_rates']
        for currency, info in exchange_rates.items():
            prompt += f"- USD/{currency}: {info['current']:.2f} ({info['change_percent']:+.2f}%)\n"
        
        prompt += "\n### 📈 거시경제 지표\n"
        
        # 거시경제 지표 추가
        economic = data['market_overview']['economic_indicators']
        for name, info in economic.items():
            prompt += f"- {name}: {info['value']:.2f}"
            if info.get('change_percent'):
                prompt += f" ({info['change_percent']:+.2f}%)"
            prompt += "\n"
        
        # 김치 프리미엄 추가
        if data.get('kimchi_premium') and len(data['kimchi_premium']) > 0:
            has_kimchi_data = any(v.get('success') for v in data['kimchi_premium'].values())
            
            if has_kimchi_data:
                prompt += "\n### 🌶️ 김치 프리미엄 (업비트 vs 글로벌)\n"
                for crypto, premium_data in data['kimchi_premium'].items():
                    if premium_data.get('success'):
                        premium = premium_data['premium_percent']
                        status = premium_data['status']
                        signal = premium_data['signal']
                        
                        emoji = "🔥" if premium > 5 else "📈" if premium > 2 else "⚖️" if premium > -2 else "📉" if premium > -5 else "❄️"
                        
                        prompt += f"- **{crypto}**: {premium:+.2f}% {emoji} ({status})\n"
                        prompt += f"  - 업비트: ₩{premium_data['upbit_price_krw']:,.0f}\n"
                        prompt += f"  - 글로벌: ${premium_data.get('binance_price_usd', premium_data.get('global_price_usd', 0)):,.2f} (₩{premium_data.get('binance_price_krw', premium_data.get('global_price_krw', 0)):,.0f})\n"
                        prompt += f"  - 신호: {signal}\n"
        
        prompt += """
### 💡 환율 및 거시경제가 포트폴리오에 미치는 영향

**중요**: 위 환율과 거시경제 지표를 반드시 분석에 포함하세요:
- **환율 (USD/KRW)**: 미국 자산 투자 시 환차손익에 직접 영향
- **VIX (변동성 지수)**: 시장 불안도. 높을수록 리스크 오프 (금 매력↑)
- **금리 (FED Rate)**: 높을수록 주식↓, 채권/예금↑, REITs↓
- **실업률**: 경제 건강도. 낮을수록 경제 강세
- **인플레이션**: 높을수록 금↑, 채권↓
- **김치 프리미엄**: 국내 암호화폐 시장의 프리미엄/디스카운트. 매수/매도 타이밍 판단에 활용

현재 이 지표들이 어떤 투자 환경을 형성하는지 명확히 설명하세요.

---

## 2. 보유 주식 분석
"""
        
        # 각 주식 정보 추가
        for stock in data['stocks']:
            symbol = stock['symbol']
            basic = stock['basic_info']
            tech = stock['technical_indicators']
            signals = stock['signals']
            
            prompt += f"### {symbol} - {stock['name']}\n\n"
            prompt += f"**현재 가격**: ${basic['current_price']:.2f} "
            prompt += f"({basic['day_change']['percent']:+.2f}%)\n\n"
            
            # 기술적 지표
            prompt += "**기술적 지표**:\n"
            if tech.get('rsi'):
                prompt += f"- RSI(14): {tech['rsi']:.2f}\n"
            
            if tech.get('moving_averages'):
                mas = tech['moving_averages']
                prompt += f"- 이동평균: "
                ma_parts = []
                if mas.get('MA20'):
                    ma_parts.append(f"MA20: ${mas['MA20']:.2f}")
                if mas.get('MA50'):
                    ma_parts.append(f"MA50: ${mas['MA50']:.2f}")
                if mas.get('MA200'):
                    ma_parts.append(f"MA200: ${mas['MA200']:.2f}")
                prompt += ", ".join(ma_parts)
                prompt += "\n"
            
            if tech.get('macd'):
                macd = tech['macd']
                prompt += f"- MACD: {macd.get('trend', 'N/A')} (히스토그램: {macd.get('histogram', 0):.2f})\n"
            
            if tech.get('bollinger_bands'):
                bb = tech['bollinger_bands']
                prompt += f"- 볼린저 밴드 위치: {bb.get('position', 0):.1f}%\n"
            
            # 매매 신호
            prompt += f"\n**매매 신호**: {signals.get('overall', 'NEUTRAL')} "
            prompt += f"(강도: {signals.get('strength', 0)}점)\n"
            
            if signals.get('details'):
                prompt += "- " + "\n- ".join(signals['details']) + "\n"
            
            prompt += "\n---\n\n"
        
        # 분석 요청 - 잼스 스타일
        exchange_rate_current = list(data['market_overview']['exchange_rates'].values())[0]['current'] if data['market_overview']['exchange_rates'] else 0
        
        prompt += f"""
---

## 🎯 잼스, 지금 분석 시작!

위 데이터를 바탕으로 **오늘의 투자 코칭 리포트**를 작성하세요.

### 📋 필수 작성 항목

#### 1️⃣ 오늘의 한 줄 요약 (Market Mood)
- 현재 시장 환경을 [공격 모드 🔥 / 방어 모드 🛡️ / 관망 모드 👀] 중 하나로 정의하고, 그 이유를 한 문장으로 설명하세요.

#### 2️⃣ 💰 자금 흐름 및 환전 지시 (Money Move)
**현재 환율: {exchange_rate_current:.2f}원**
- 환율이 1,350원 이하면 "적극 환전" 지시
- 환율이 1,400원 이상이면 "필요량만 환전" 지시
- 토스증권 낮 시간대(환율 우대) 활용 강조
- 만기 자금이 있다면 어느 종목에 집중 투자할지 명확히 지시

**예시:**
"현재 환율 1,432원으로 높은 편입니다. 급하지 않다면 환전은 1,400원 아래로 떨어질 때까지 기다리세요. 대신 보유 달러가 있다면 NVDA가 좋은 진입 시점이니 오늘 바로 매수하세요."

#### 3️⃣ 📊 개별 종목 투자 의견 (Stock-by-Stock Action)

**중요**: 위에 나열된 **모든 보유 종목**에 대해 개별적으로 구체적인 투자 의견을 제시하세요.
각 종목마다 다음 형식을 따르세요:

**[종목명] - 투자 의견**
- **현재 상태**: [기술적 상태 요약 - 정배열/역배열, RSI 수준, 추세 등]
- **오늘의 액션**: [구체적 행동 지시]
  - 예: "✅ 적극 매수 - 여유자금 10% 투입"
  - 예: "⏸️ 매수 중단 - 현재 보유분만 유지"
  - 예: "📈 추가 매수 - 2만원 분할 매수"
  - 예: "⚠️ 관망 - 20일선 돌파 시까지 대기"
  - 예: "🔴 일부 매도 고려 - 과열 구간"
- **이유**: [왜 이런 판단을 내렸는지 1-2문장으로 설명]

**예시:**
```
**AAPL - Apple Inc.**
- 현재 상태: 20일선 아래 위치, RSI 50 중립, 단기 조정 중
- 오늘의 액션: ⏸️ 신규 매수 중단 - 보유분만 유지
- 이유: 단기 이평선이 하향 전환했으나 장기 추세는 양호. 20일선 재돌파 확인 후 재진입 권장.

**NVDA - NVIDIA Corporation**
- 현재 상태: 정배열 유지, RSI 59 양호, 상승 추세 지속
- 오늘의 액션: ✅ 적극 매수 - 여유자금 15% 투입
- 이유: AI 섹터 강세 지속, 기술적으로 건강한 상승. 지금이 추가 진입 적기.

**BTC-USD - Bitcoin**
- 현재 상태: RSI 19 과매도, 단기 조정, MA20 > MA50 정배열 유지
- 오늘의 액션: 📈 분할 매수 - 여유자금 10% + DCA 유지
- 이유: 과매도 구간에서 반등 가능성 높음. 정배열 유지로 중장기 추세 양호.
```

**각 종목에 대해 이런 식으로 구체적인 투자 의견을 작성하세요!**

#### 4️⃣ 🚀 계좌별 액션 플랜 (Specific Action)

**각 계좌마다 구체적인 지시를 내려주세요:**

**📱 ISA 계좌 (국내/해외 ETF)**
- 예: "TIGER 미국나스닥100은 정배열 유지 중입니다. 오늘 2만원 추가 매수하세요."
- 예: "ACE KRX금현물은 VIX가 높아 헤지 효과가 있습니다. 여유자금의 5%를 오늘 분할 진입하세요."

**💼 토스증권 (해외 주식)**
- 예: "AAPL은 20일선 아래로 떨어졌습니다. 신규 매수는 쉬고 관망하세요."
- 예: "NVDA가 과열권(RSI 75 초과)입니다. 추가 매수 중단하고 보유분은 유지하세요."

**🏦 연금/IRP 계좌 (장기 투자)**
- 예: "시장 변동성이 크니 국채 ETF 비중을 계획보다 5% 늘리세요."
- 예: "배당주 ETF는 지금이 저점 매수 기회입니다. 분할 매수 진행하세요."

**🪙 업비트 (암호화폐)**
- 예: "비트코인이 정배열을 유지 중입니다. 주 1회 정기 매수 외에 여유자금 10%를 오늘 추가 진입하세요."
- 예: "이더리움이 역배열 진입했습니다. 신규 매수 즉시 중단하고 관망하세요."

#### 5️⃣ ⚠️ 리스크 알림 & 멘탈 케어
- VIX, 환율, 기술적 지표 중 **가장 주의해야 할 리스크** 1-2개를 명확히 경고
- 불안할 때 어떻게 대응해야 하는지 멘탈 관리 조언 포함

**예시:**
"VIX가 17.44로 상승 중입니다. 시장 변동성이 커질 수 있으니 신규 매수는 분할로 진행하고, 한 번에 몰빵하지 마세요. 지금은 조급하게 움직일 때가 아닙니다."

---

## ✅ 작성 시 반드시 지켜야 할 원칙

### 💰 수익 극대화 전략
1. **공격적이되 전략적으로**: 보수적 투자가 아닌, 기회를 포착하는 공격적 투자
2. **여유자금 100% 활용**: DCA는 기본, 여유자금으로 알파 수익 창출
3. **타이밍 놓치지 않기**: "나중에", "천천히"가 아닌 "오늘", "지금 바로" 지시
4. **구체적 투입 비율**: "조금", "적당히"가 아닌 "10%", "2만원", "5% 증액" 등 명확한 수치

### 📝 작성 스타일
1. **확신에 찬 어조 사용**: "~하세요", "~는 쉬어가세요", "지금이 기회입니다" (❌ "~해보세요", "~인 것 같습니다")
2. **구체적인 금액/비율 제시**: "2만원 매수", "여유자금의 10%", "5% 비중 확대"
3. **계좌별 맞춤 지시**: ISA/토스/연금/업비트 각각에 대해 개별 액션 플랜 제공
4. **개별 종목별 투자 의견 필수**: 모든 보유 종목에 대해 구체적 액션 제시
5. **환율 전략 필수 포함**: 오늘 환전할지 말지 명확히 지시

### 🎯 핵심 메시지
- "기회는 준비된 자에게 온다" - 좋은 진입점을 놓치지 말 것
- "분산은 기본, 집중은 알파" - 핵심 종목에 과감하게 투자
- "리스크는 관리하되, 기회는 놓치지 말 것" - 공격적이되 무모하지 않게

---

**자, 잼스! 위 데이터를 분석해서 사용자에게 오늘의 투자 코칭 리포트를 작성하세요.**
"""

        
        return prompt
    
    def to_json(self, data: Dict, indent: int = 2) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(data, indent=indent, ensure_ascii=False)
    
    def to_telegram_message(self, data: Dict) -> str:
        """텔레그램 메시지 형식으로 변환 (HTML) - 상세 버전"""
        
        msg = f"<b>📊 주식 시장 분석 리포트</b>\n"
        msg += f"<i>{data['analysis_date']}</i>\n\n"
        
        # 환율 정보
        msg += "<b>💱 환율</b>\n"
        exchange_rates = data['market_overview']['exchange_rates']
        for currency, info in exchange_rates.items():
            change_emoji = "📈" if info['change_percent'] > 0 else "📉" if info['change_percent'] < 0 else "➡️"
            msg += f"{change_emoji} USD/{currency}: {info['current']:.2f} ({info['change_percent']:+.2f}%)\n"
        
        # 거시경제 요약
        if data['market_overview']['economic_indicators']:
            msg += f"\n<b>📈 거시경제 지표</b>\n"
            economic = data['market_overview']['economic_indicators']
            
            # VIX 특별 처리
            if 'VIX' in economic:
                vix_info = economic['VIX']
                vix_value = vix_info['value']
                vix_status = self._get_vix_status(vix_value)
                
                msg += f"• VIX: {vix_value:.2f} "
                msg += f"{vix_status['emoji']} ({vix_status['status']})\n"
                
                # VIX 제외한 나머지 지표 (최대 2개)
                other_indicators = {k: v for k, v in economic.items() if k != 'VIX'}
                for name, info in list(other_indicators.items())[:2]:
                    msg += f"• {name}: {info['value']:.2f}\n"
            else:
                # VIX 없으면 상위 3개 표시
                for name, info in list(economic.items())[:3]:
                    msg += f"• {name}: {info['value']:.2f}\n"
        
        # 김치 프리미엄 정보
        if data.get('kimchi_premium') and len(data['kimchi_premium']) > 0:
            msg += f"\n<b>🌶️ 김치 프리미엄</b>\n"
            has_content = False
            for crypto, premium_data in data['kimchi_premium'].items():
                if premium_data.get('success'):
                    has_content = True
                    premium = premium_data['premium_percent']
                    
                    # 이모지 선택
                    if premium > 5:
                        emoji = "🔥"  # 높은 프리미엄
                    elif premium > 2:
                        emoji = "📈"  # 프리미엄
                    elif premium > -2:
                        emoji = "⚖️"  # 균형
                    elif premium > -5:
                        emoji = "📉"  # 디스카운트
                    else:
                        emoji = "❄️"  # 높은 디스카운트
                    
                    msg += f"{emoji} <b>{crypto}</b>: {premium:+.1f}% ({premium_data['status']})\n"
            
            # 데이터가 없으면 타이틀도 제거
            if not has_content:
                msg = msg.replace(f"\n<b>🌶️ 김치 프리미엄</b>\n", "")
        
        # 주식 상세 정보
        msg += f"\n<b>{'='*30}</b>\n"
        msg += f"<b>🎯 보유 주식 분석</b>\n"
        msg += f"<b>{'='*30}</b>\n\n"
        
        for idx, stock in enumerate(data['stocks'], 1):
            signal = stock['signals'].get('overall', 'NEUTRAL')
            emoji = self._get_signal_emoji(signal)
            
            basic = stock['basic_info']
            tech = stock['technical_indicators']
            
            # 헤더
            msg += f"{emoji} <b>[{idx}] {stock['symbol']}</b>\n"
            msg += f"<i>{stock['name']}</i>\n"
            
            # 섹터
            if basic.get('sector'):
                msg += f"📂 <b>섹터:</b> {basic['sector']}\n"
            
            # 현재 가격
            change_emoji = "🔺" if basic['day_change']['percent'] > 0 else "🔻" if basic['day_change']['percent'] < 0 else "▪️"
            msg += f"💰 <b>현재가:</b> ${basic['current_price']:.2f} {change_emoji} {basic['day_change']['percent']:+.2f}%\n"
            
            # RSI 점수 (과열/침체 표시)
            rsi = tech.get('rsi')
            if rsi:
                if rsi >= 70:
                    rsi_status = "🔴 과매수"
                elif rsi >= 60:
                    rsi_status = "🟠 과열"
                elif rsi <= 30:
                    rsi_status = "🟢 과매도"
                elif rsi <= 40:
                    rsi_status = "🟡 침체"
                else:
                    rsi_status = "⚪ 중립"
                
                msg += f"📊 <b>RSI(14):</b> {rsi:.1f} ({rsi_status})\n"
            
            # 정배열/역배열
            ma_align = tech.get('ma_alignment', {})
            if ma_align:
                alignment = ma_align.get('alignment', 'N/A')
                if alignment == "정배열":
                    align_emoji = "🟢"
                elif alignment == "역배열":
                    align_emoji = "🔴"
                else:
                    align_emoji = "🟡"
                
                msg += f"📈 <b>이평선:</b> {align_emoji} {alignment}\n"
                
                # 장기 이평선 정보 (MA20, MA50, MA200) + 현재가 대비 위치
                current_price = basic.get('current_price', 0)
                ma20 = ma_align.get('ma20')
                ma50 = ma_align.get('ma50')
                ma200 = ma_align.get('ma200')
                
                if ma20 and ma50 and current_price:
                    ma_info = f"   MA20: ${ma20:.2f}"
                    
                    # MA20 대비 위치
                    if current_price > ma20:
                        ma_info += f" ⬆️"
                    else:
                        ma_info += f" ⬇️"
                    
                    ma_info += f" | MA50: ${ma50:.2f}"
                    
                    # MA50 대비 위치
                    if current_price > ma50:
                        ma_info += f" ⬆️"
                    else:
                        ma_info += f" ⬇️"
                    
                    if ma200:
                        ma_info += f" | MA200: ${ma200:.2f}"
                        # MA200 대비 위치
                        if current_price > ma200:
                            ma_info += f" ⬆️"
                        else:
                            ma_info += f" ⬇️"
                    
                    msg += f"<i>{ma_info}</i>\n"
                
                # 골든크로스/데드크로스
                cross_signal = ma_align.get('cross_signal', 'N/A')
                if "골든크로스" in cross_signal:
                    cross_emoji = "✨"
                elif "데드크로스" in cross_signal:
                    cross_emoji = "💀"
                elif "임박" in cross_signal:
                    cross_emoji = "⚠️"
                else:
                    cross_emoji = "➡️"
                
                msg += f"⚡ <b>크로스:</b> {cross_emoji} {cross_signal}\n"
            
            # 이격도
            disparity = tech.get('disparity', {})
            if disparity:
                disp_value = disparity.get('disparity_20', 100)
                disp_status = disparity.get('status', 'N/A')
                
                if disp_status == "과열":
                    disp_emoji = "🔥"
                elif disp_status == "강세":
                    disp_emoji = "📈"
                elif disp_status == "침체":
                    disp_emoji = "❄️"
                elif disp_status == "약세":
                    disp_emoji = "📉"
                else:
                    disp_emoji = "➡️"
                
                msg += f"📐 <b>이격도(20):</b> {disp_value:.1f}% {disp_emoji} {disp_status}\n"
            
            # 매매 신호
            strength = stock['signals'].get('strength', 0)
            if strength > 30:
                signal_text = "🟢🟢 강력 매수"
            elif strength > 10:
                signal_text = "🟢 매수"
            elif strength < -30:
                signal_text = "🔴🔴 강력 매도"
            elif strength < -10:
                signal_text = "🔴 매도"
            else:
                signal_text = "⚪ 관망"
            
            msg += f"🎯 <b>신호:</b> {signal_text} ({strength:+d}점)\n"
            
            # 구분선
            if idx < len(data['stocks']):
                msg += f"\n{'-'*30}\n\n"
        
        msg += f"\n<i>💡 상세 분석은 첨부된 JSON 파일을 Gemini에 업로드하세요</i>"
        
        return msg
    
    def _get_signal_emoji(self, signal: str) -> str:
        """매매 신호에 따른 이모지 반환"""
        emoji_map = {
            'STRONG_BUY': '🟢🟢',
            'BUY': '🟢',
            'NEUTRAL': '⚪',
            'SELL': '🔴',
            'STRONG_SELL': '🔴🔴'
        }
        return emoji_map.get(signal, '⚪')
    
    def _get_vix_status(self, vix_value: float) -> Dict[str, str]:
        """VIX 값에 따른 시장 상태 반환"""
        if vix_value < 15:
            return {
                'status': '극도의 안도',
                'emoji': '😌',
                'color': '🟢'
            }
        elif vix_value < 25:
            return {
                'status': '정상 범위',
                'emoji': '😐',
                'color': '⚪'
            }
        elif vix_value < 35:
            return {
                'status': '경계 및 공포',
                'emoji': '😰',
                'color': '🟡'
            }
        else:
            return {
                'status': '패닉',
                'emoji': '😱',
                'color': '🔴'
            }



# 테스트 코드
if __name__ == "__main__":
    formatter = GeminiFormatter()
    
    # 샘플 데이터
    sample_stocks = {
        'stocks': {
            'AAPL': {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'current_price': 180.0,
                'previous_close': 175.0,
                'volume': 50000000,
                'market_cap': 2800000000000,
                'pe_ratio': 28.5,
                'sector': 'Technology',
                'success': True,
                'source': 'yfinance'
            }
        }
    }
    
    sample_tech = {
        'technical_analysis': {
            'AAPL': {
                'rsi': 55.3,
                'moving_averages': {'MA20': 178.0, 'MA50': 172.0, 'MA200': 165.0},
                'macd': {'trend': 'bullish', 'histogram': 1.5},
                'bollinger_bands': {'position': 65.0},
                'signals': {'overall': 'BUY', 'strength': 25, 'details': ['RSI 중립', '단기 상승 추세']}
            }
        }
    }
    
    sample_exchange = {
        'exchange_rates': {
            'KRW': {
                'current_rate': 1320.5,
                'change_percent': -0.5,
                'source': 'ExchangeRate-API',
                'success': True
            }
        }
    }
    
    sample_macro = {
        'macro_indicators': {
            'VIX': {
                'current_value': 16.5,
                'change_percent': -2.3,
                'success': True
            }
        }
    }
    
    result = formatter.format_for_gemini(
        sample_stocks,
        sample_tech,
        sample_exchange,
        sample_macro
    )
    
    print("=== Gemini Prompt ===")
    print(result['gemini_prompt'])
    
    print("\n\n=== Telegram Message ===")
    print(formatter.to_telegram_message(result))
