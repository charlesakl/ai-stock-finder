"""Historical price-channel research visualization, not investment instructions."""
import pandas as pd


def calculate_zones(close, window=20):
    prices = pd.to_numeric(close, errors='coerce').dropna().astype(float)
    avg = prices.rolling(window, min_periods=window).mean()
    std = prices.rolling(window, min_periods=window).std()
    lower, upper = avg - 2 * std, avg + 2 * std
    delta = prices.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rsi = 100 - 100 / (1 + gain / loss.replace(0, float('nan')))
    rsi = rsi.mask((loss == 0) & (gain > 0), 100).mask((loss == 0) & (gain == 0), 50)
    # Zones are descriptive of historical conditions; no forward-looking claims.
    buy_watch = (prices <= lower) & (rsi < 35)
    sell_watch = (prices >= upper) & (rsi > 65)
    df = pd.DataFrame({'Price': prices, 'Lower band': lower, '20-day average': avg,
                       'Upper band': upper, 'RSI': rsi, 'Potential lower zone': buy_watch,
                       'Potential upper zone': sell_watch}).dropna()
    df.index = pd.to_datetime(df.index)
    df.index.name = 'Date'
    return df


def render_price_chart(st, ticker, close, horizon):
    import altair as alt
    df = calculate_zones(close)
    if df.empty:
        st.info('Not enough daily history to draw the price-zone chart.')
        return
    st.markdown('🟢 **BUY WATCH (lower price zone)** = possible research entry · 🔴 **SELL WATCH (upper price zone)** = possible research exit. These are historical conditions, **not actual tops/bottoms or trade instructions**.')
    show_markers = st.checkbox('Show BUY / SELL watch markers', value=True, key=f'watch_markers_{ticker}')
    view = df.tail(126 if horizon.startswith('Short') else 252 if horizon.startswith('Medium') else 504).reset_index()
    base = alt.Chart(view).encode(x=alt.X('Date:T', title='Trading date'))
    band = base.mark_area(opacity=.14, color='#64748b').encode(y=alt.Y('Lower band:Q', title='Adjusted share price ($)', scale=alt.Scale(zero=False)), y2='Upper band:Q')
    price = base.mark_line(color='#2563eb', strokeWidth=2).encode(y='Price:Q', tooltip=['Date:T', alt.Tooltip('Price:Q', format='.2f'), alt.Tooltip('RSI:Q', format='.1f')])
    avg = base.mark_line(color='#64748b', strokeDash=[5, 4]).encode(y='20-day average:Q')
    low = base.transform_filter(alt.datum['Potential lower zone'] == True).mark_point(shape='triangle-up', size=120, filled=True, color='#16a34a').encode(y='Price:Q', tooltip=['Date:T', 'Price:Q', 'RSI:Q'])
    high = base.transform_filter(alt.datum['Potential upper zone'] == True).mark_point(shape='triangle-down', size=120, filled=True, color='#dc2626').encode(y='Price:Q', tooltip=['Date:T', 'Price:Q', 'RSI:Q'])
    low_labels = base.transform_filter(alt.datum['Potential lower zone'] == True).mark_text(text='BUY', dy=17, fontSize=10, fontWeight='bold', color='#16a34a').encode(y='Price:Q')
    high_labels = base.transform_filter(alt.datum['Potential upper zone'] == True).mark_text(text='SELL', dy=-17, fontSize=10, fontWeight='bold', color='#dc2626').encode(y='Price:Q')
    layers = (band + avg + price + low + high + low_labels + high_labels) if show_markers else (band + avg + price)
    st.altair_chart(layers.properties(height=370), use_container_width=True)
    last = df.iloc[-1]
    if bool(last['Potential lower zone']):
        status = 'Lower-price watch zone (not a buy signal)'
    elif bool(last['Potential upper zone']):
        status = 'Upper-price watch zone (not a sell signal)'
    else:
        status = 'No extreme price-zone condition today'
    st.caption(f"Latest chart condition: **{status}** · RSI {last['RSI']:.1f}. "
               'Green ▲ = historical lower-band/low-RSI watch; red ▼ = historical upper-band/high-RSI watch. '
               'Markers are not trades, do not predict bottoms or tops, and can fail during trends. '
               'Bands use adjusted daily closing prices and a 20-day rolling average ±2 standard deviations.')
