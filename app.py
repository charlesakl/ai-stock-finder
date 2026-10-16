import os
from dotenv import load_dotenv
load_dotenv()
from agents import gather_evidence, analyze
import pandas as pd
import streamlit as st
import yfinance as yf
from research import HORIZONS, BANDS, evaluate, select_candidates
from usage_limiter import remaining, reserve, paid_enabled

st.set_page_config(page_title='AI Stock Finder', page_icon='📈', layout='wide')
st.title('📈 AI Stock Finder')
st.caption('Phase 11 · Stock research, cached AI analysis, and BUY/SELL watch-zone charts')

st.warning('Market data may be delayed or incomplete. A price decline is not proof of undervaluation. The quantitative score is a screening heuristic, NOT an LLM recommendation or prediction.')
DEFAULT = 'F, SOFI, PFE, T, PLTR, SNAP, INTC, BAC, C, UBER, PYPL, DIS, NKE, SBUX, GOOGL, AMD, NVDA, AAPL, MSFT, CSCO, RIVN, LCID, HOOD, DKNG, WBD, HIMS, GM, CVS, PINS, ROKU'
with st.sidebar:
    st.header('Research settings')
    ai_mode = st.radio('Research mode', ['Free Research', 'AI Research', 'Advanced AI Research'], index=0,
        help='Free: no OpenAI calls. AI Research: one manual AI checklist. Advanced: optional six-agent reviews and committee.')
    mode_descriptions = {
        'Free Research': (
            'Screen stocks, review available financial metrics and technical indicators, and explore historical '
            'BUY/SELL watch zones. No OpenAI API calls are made in this mode.'
        ),
        'AI Research': (
            'Includes Free Research tools plus an optional single AI analyst checklist for individual stocks. '
            'AI runs only when you click Analyze; repeat requests can use the 7-day cache. API charges may apply.'
        ),
        'Advanced AI Research': (
            'Includes Free Research tools plus optional six-agent stock reviews and an Investment Committee '
            'comparison. Each paid analysis must be started manually; API charges can be higher.'
        ),
    }
    st.caption(mode_descriptions[ai_mode])
    os.environ['AI_CACHE_HOURS'] = '168'
    st.caption('AI responses cached for 7 days; market prices refresh separately.')
    st.caption('Paid research only runs when you click its dedicated button.')
    # Preserve detailed results and original screening controls in all modes.
    view_mode = 'Advanced'
    horizon_options = list(HORIZONS)
    default_horizon = next((i for i, name in enumerate(horizon_options) if '6' in name and 'month' in name.lower()), 0)
    horizon = st.selectbox('Investment horizon', horizon_options, index=default_horizon)
    with st.expander('Screening Settings', expanded=False):
        universe_mode = st.radio('Stock universe', ['S&P 500 (approximately 500 companies)', 'Custom tickers'], index=0)
        max_stocks = st.slider('Maximum companies to scan', 100, 550, 500, step=50) if universe_mode.startswith('S&P') else 75
        tickers_text = st.text_area('Custom ticker universe (comma-separated)', DEFAULT, height=120)
        phase6_enabled = st.checkbox('Analyze financial health and technical indicators', value=True,
            help='Additional research checks on shortlisted stocks using available third-party financial summaries and historical price data. This is not an audit or confirmation of fair value.')
        st.caption('Checks available valuation, growth, profitability and financial-strength measures alongside price trends, momentum and volatility for shortlisted stocks. Results help prioritize further research; they do not verify audited filings or predict returns. No OpenAI API calls in Free Research.')
        st.caption('The custom list is used only when Custom tickers is selected. Screening may require market-data downloads, but no OpenAI API calls.')
    use_ai = ai_mode == 'AI Research'
    research_enabled = False
    multi_enabled = ai_mode == 'Advanced AI Research'
    auto_research = False
    auto_committee = False
    run = st.button('Find opportunities', type='primary', use_container_width=True)
    if ai_mode != 'Free Research':
        # This identity is intentionally local-only. Public deployments require
        # real authentication and a persistent shared database.
        local_user = os.getenv('LOCAL_USER_ID', 'local-owner')
        if not paid_enabled():
            st.warning('Paid AI disabled on this deployment.')
        else:
            st.caption(f'Daily {ai_mode} requests remaining: {remaining(local_user, ai_mode)} / {5 if ai_mode == "AI Research" else 2} (resets UTC)')
        st.caption('OpenAI API usage is billed separately from ChatGPT. Limits are workflow counts, not dollar limits.')


def allow_paid(mode):
    try:
        ok, message = reserve(os.getenv('LOCAL_USER_ID', 'local-owner'), mode)
    except Exception:
        st.error('Unable to verify AI quota. Paid request blocked for safety.')
        return False
    if not ok:
        st.warning(message)
    return ok


@st.cache_data(ttl=1800, show_spinner=False)
def load_prices(ticker):
    frame = yf.download(ticker, period='2y', interval='1d', auto_adjust=True, progress=False, threads=False)
    if frame is None or frame.empty:
        return None
    close = frame['Close']
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close

def ai_commentary(candidate):
    try:
        from openai import OpenAI
        key = os.getenv('OPENAI_API_KEY') or st.secrets.get('OPENAI_API_KEY')
        if not key: return 'OpenAI key not configured. AI analysis skipped.'
        client = OpenAI(api_key=key)
        prompt = (f'Provide a cautious 100-word research checklist for {candidate.ticker} at ${candidate.price}, '
                  f'as of {candidate.asof}, horizon {candidate.horizon}. Price change 30d {candidate.change_30d_pct}%, '
                  f'52-week drawdown {candidate.drawdown_52w_pct}%, volatility {candidate.volatility_annual_pct}%. '
                  'You have NO access to current news, earnings, filings or valuation data. Explicitly state this; '
                  'do not invent sources, catalysts, financial metrics, price targets, or claim this is a buy. '
                  'Suggest concrete items to verify before making an investment decision.')
        from ai_cache import key_for, load, save
        model = os.getenv('OPENAI_MODEL','gpt-4.1-mini')
        key_cache = key_for('budget-checklist-v2', model, 'concise-checklist', prompt)
        cached = load(key_cache)
        if cached is not None: return cached['text'] + '\n\n(Cached response)'
        resp = client.responses.create(model=model,input=prompt,max_output_tokens=350)
        answer = resp.output_text or 'No AI text returned.'
        save(key_cache, {'text': answer})
        return answer
    except Exception as e:
        return f'AI commentary unavailable ({type(e).__name__}). Market screen remains available.'

if run:
    if universe_mode.startswith('S&P'):
        try:
            from universe import load_sp500
            with st.spinner('Loading current S&P 500 constituents...'):
                tickers = load_sp500()[:max_stocks]
        except Exception as exc:
            st.error(f'Could not retrieve the S&P 500 list: {exc}. Switch to Custom tickers or retry.')
            st.stop()
    else:
        tickers = list(dict.fromkeys(t.strip().upper() for t in tickers_text.split(',') if t.strip()))[:75]
    if not tickers:
        st.error('No tickers to scan.')
        st.stop()
    from bulk_screen import screen_universe
    progress = st.progress(0)
    with st.spinner(f'Scanning {len(tickers)} stocks in batches; this may take several minutes...'):
        found, errors = screen_universe(tickers, horizon, progress.progress)
    st.session_state['sec_reports'] = {}
    st.session_state['quality_reports'] = {}
    st.session_state['quality_errors'] = {}
    st.session_state['quality_mode'] = phase6_enabled
    if phase6_enabled:
        from quality import shortlist_universe, review
        shortlist_items = shortlist_universe(found, limit=24, per_band_floor=3)
        with st.spinner(f'Phase 6: checking financial and technical evidence for {len(shortlist_items)} shortlisted stocks...'):
            for candidate in shortlist_items:
                try:
                    st.session_state['quality_reports'][candidate.ticker] = review(candidate)
                except Exception as exc:
                    st.session_state['quality_errors'][candidate.ticker] = f'{type(exc).__name__}: {exc}'
    st.session_state['results'] = (found, errors, horizon)
    st.session_state['scan_count'] = len(tickers)
    st.session_state['auto_review_pending'] = auto_research
    st.session_state['auto_committee_pending'] = auto_committee and auto_research
    st.session_state.pop('committee_report', None)
    for key in list(st.session_state):
        if key.startswith(('multi_', 'evidence_', 'assessment_', 'backtest_result_')):
            del st.session_state[key]

if 'results' not in st.session_state:
    st.info('Choose a time horizon and click **Find opportunities** to begin.')
    st.stop()
found, errors, analyzed_horizon = st.session_state['results']
st.subheader(f'Screen results — {analyzed_horizon}')
st.caption(f"Scanned {st.session_state.get('scan_count', '?')} tickers; {len(found)} passed price/history filters; {len(errors.get('excluded_by_filters', []))} excluded by filters; {len(errors.get('data_unavailable', []))} download/processing failures.")
st.caption('Only the latest completed screen is shown. Run again after changing settings.')
if isinstance(errors, dict) and view_mode == 'Advanced':
    with st.expander('Phase 7 scan diagnostics: excluded vs unavailable'):
        st.write('Excluded by price/history filters:', len(errors.get('excluded_by_filters', [])))
        st.write('Download/processing failures:', len(errors.get('data_unavailable', [])))
        st.write('Unavailable tickers:', ', '.join(errors.get('data_unavailable', [])) or 'None')
if st.session_state.get('quality_mode'):
    from quality import select_quality_overall
    quality_reports = st.session_state.get('quality_reports', {})
    selected = select_quality_overall(found, quality_reports, analyzed_horizon, limit=3)
    if view_mode == 'Advanced':
        st.subheader('Financial quality and research eligibility')
        st.caption('The strongest three research leads are selected across all price bands, not one per band. Short emphasizes price stabilization; Medium balances quality and momentum; Long emphasizes quality.')
    if view_mode == 'Advanced':
        st.caption('Checks use Yahoo Finance summary data, not audited filing verification. The quality score is a transparent heuristic, not a fair-value estimate or a buy signal.')
    if quality_reports and view_mode == 'Advanced':
        quality_table = pd.DataFrame([{
            'Ticker':r['ticker'], 'Status':r['status'], 'Quality points / 100':r['quality_points'],
            'Evidence coverage / 100':r['coverage_pct'], 'Sector model':r.get('sector_model',''), 'Flags':'; '.join(r['flags']),
            'Missing':'; '.join(r['missing']), 'Data retrieved (UTC)':r['retrieved_at']}
            for r in quality_reports.values()]).sort_values('Quality points / 100',ascending=False)
        st.dataframe(quality_table, hide_index=True, use_container_width=True)
        st.download_button('Download quality checks CSV', quality_table.to_csv(index=False), 'quality_checks.csv', 'text/csv', key='quality_export')
    if st.session_state.get('quality_errors'):
        st.warning('Quality lookups unavailable: ' + '; '.join(f'{k}: {v}' for k,v in st.session_state['quality_errors'].items()))
    if not any(selected.values()):
        st.warning('No stock passed all Phase 7 quality gates. This is not a recommendation to buy any candidate. Disable Phase 6 to view original quantitative finalists.')
else:
    from quality import select_screen_overall
    selected = select_screen_overall(found, limit=3)
selected_tickers = [item.ticker for item in selected.values() if item]
# Fetch filing evidence only for finalists, never for all 500 stocks.
# The results are cached in session state for this scan and reused by all AI agents.
if os.getenv('SEC_USER_AGENT') and selected_tickers:
    from sec_evidence import fetch_sec_evidence
    for ticker in selected_tickers:
        if ticker not in st.session_state.setdefault('sec_reports', {}):
            with st.spinner(f'Checking SEC EDGAR data for {ticker}...'):
                st.session_state['sec_reports'][ticker] = fetch_sec_evidence(ticker)

if False and ai_mode == 'Advanced AI Research' and st.session_state.get('auto_review_pending'):
    st.session_state['auto_review_pending'] = False
    if not os.getenv('OPENAI_API_KEY'):
        st.warning('OPENAI_API_KEY missing; AI review skipped. Quantitative candidates are shown below.')
    else:
        from multi_agents import run_research
        for item in selected.values():
            if item:
                try:
                    with st.spinner(f'Running six-agent review for {item.ticker}...'):
                        st.session_state[f'multi_{item.ticker}'] = run_research(item, quality_report=st.session_state.get('quality_reports', {}).get(item.ticker), sec_report=st.session_state.get('sec_reports', {}).get(item.ticker))
                except Exception as exc:
                    st.error(f'AI review failed for {item.ticker}: {type(exc).__name__}: {exc}')

# Phase 5: compare only completed reviews for current finalists.
from investment_committee import compare_candidates
current_reports = {ticker: st.session_state.get(f'multi_{ticker}') for ticker in selected_tickers}
completed_reports = {ticker: report for ticker, report in current_reports.items() if report}
if False and ai_mode == 'Advanced AI Research' and st.session_state.get('auto_committee_pending'):
    st.session_state['auto_committee_pending'] = False
    if len(completed_reports) >= 2 and os.getenv('OPENAI_API_KEY'):
        try:
            with st.spinner('Investment committee comparing completed six-agent reports...'):
                st.session_state['committee_report'] = compare_candidates(completed_reports, analyzed_horizon)
        except Exception as exc:
            st.error(f'Investment committee failed: {type(exc).__name__}: {exc}')
    else:
        st.warning('Committee needs at least two completed six-agent reports and an OpenAI API key.')

committee = st.session_state.get('committee_report')
# Always put the concise, comparable three-stock summary above the detailed results.
st.subheader('Top stock research candidates')
rankings = {r.get('ticker'): r for r in (committee or {}).get('rankings', [])}
summary_rows = []
for band, item in selected.items():
    if item is None:
        continue
    r = rankings.get(item.ticker, {})
    decision = (completed_reports.get(item.ticker) or {}).get('decision', {})
    raw_status = r.get('stance') or decision.get('status') or 'Preliminary screen'
    status = ('Avoid for now' if 'avoid' in raw_status.lower() else
              'More research needed' if raw_status.lower() in ('insufficient evidence', 'watch') else
              'Research candidate — verify' if raw_status.lower() == 'research candidate' else
              'Preliminary screen only')
    sec_status = st.session_state.get('sec_reports', {}).get(item.ticker, {}).get('status', 'not_configured')
    summary_rows.append({'Rank': r.get('rank'), 'Stock': item.ticker, 'Price': f'${item.price:.2f}',
                         '30-day change': f'{item.change_30d_pct:+.1f}%', 'Time horizon': analyzed_horizon,
                         'Recommendation': status,
                         'SEC data': 'Available — check filings' if sec_status == 'available' else 'Not verified'})
summary_rows.sort(key=lambda x: (x['Rank'] if isinstance(x['Rank'], int) else 999, x['Stock']))
for i, row in enumerate(summary_rows, 1):
    if row['Rank'] is None:
        row['Rank'] = i
if summary_rows:
    st.dataframe(pd.DataFrame(summary_rows), hide_index=True, use_container_width=True,
                 column_config={'Stock': st.column_config.TextColumn('Stock', width='small'),
                                'Recommendation': st.column_config.TextColumn('Recommendation', width='medium')})
    st.caption('Rank = priority for further research, NOT a buy rating or predicted return. SEC data availability does not mean complete filing verification.')
    with st.expander('How finalists were selected (and alternatives)', expanded=False):
        st.write('The scanner considers eligible companies across **all price bands**. It checks a diversified shortlist, ranks eligible candidates using the selected investment horizon, then sends the top three to AI research. This does not guarantee the top three in the entire market because fundamental data is checked only for the shortlist.')
        if st.session_state.get('quality_mode'):
            from quality import rank_quality_universe
            comparison = rank_quality_universe(found, st.session_state.get('quality_reports', {}), analyzed_horizon)
            st.dataframe(pd.DataFrame(comparison[:12]), hide_index=True, use_container_width=True)
        else:
            st.write('Financial verification was disabled; rankings use only the preliminary screen.')
    st.subheader('📈 BUY low / SELL high — historical watch-zone chart')
    st.caption('Explore where a stock was historically near the lower or upper edge of its recent price range. This is **not** a prediction of when to buy or sell.')
    chart_ticker = st.selectbox('Chart a finalist', [row['Stock'] for row in summary_rows], key='price_zone_stock')
    try:
        from price_zones import render_price_chart
        chart_close = load_prices(chart_ticker)
        if chart_close is not None:
            render_price_chart(st, chart_ticker, chart_close, analyzed_horizon)
        else:
            st.info('Price history unavailable for this chart.')
    except Exception as exc:
        st.warning(f'Chart unavailable ({type(exc).__name__}). Research results remain available.')
else:
    st.info('No eligible candidates were found. No recommendation is made.')
if view_mode == 'Simple':
    st.subheader('Your results')
    all_items = [(band, item) for band, item in selected.items() if item is not None]
    ranked = {r.get('ticker'): r for r in (committee or {}).get('rankings', [])}
    all_items.sort(key=lambda pair: (
        ranked.get(pair[1].ticker, {}).get('rank', 999),
        -pair[1].score,
    ))
    if not all_items:
        st.info('No stocks met the research criteria in this scan. This is a valid outcome.')
    elif committee:
        st.info(f"We scanned {st.session_state.get('scan_count', '?')} companies and selected "
                f"{len(all_items)} for further research. These are research priorities, not buy recommendations.")
        st.write('**Overall conclusion:** No candidate has a confirmed market bottom. '
                 'Review the evidence and risks before considering an investment.')
    else:
        st.info(f"{len(all_items)} preliminary candidates were found. "
                "The AI comparison is not yet available; these are not buy recommendations.")
    def plain_status(raw):
        value = (raw or '').strip().lower()
        if 'avoid' in value: return 'Avoid for now'
        if 'insufficient' in value or 'watch' in value: return 'More research needed'
        if 'research candidate' in value: return 'Worth investigating'
        return 'Preliminary candidate'

    for i, (band, item) in enumerate(all_items, 1):
        q = st.session_state.get('quality_reports', {}).get(item.ticker, {})
        r = ranked.get(item.ticker, {})
        report = completed_reports.get(item.ticker) or {}
        decision = report.get('decision', {}) if isinstance(report, dict) else {}
        status = plain_status(r.get('stance') or decision.get('status'))
        risks = r.get('risks') or decision.get('risks') or q.get('flags') or []
        checks = r.get('entry_conditions') or decision.get('additional_checks') or q.get('missing') or []
        with st.container(border=True):
            st.markdown(f"### #{i} · {item.ticker} — ${item.price:.2f}")
            st.caption(f'{band} · As of {item.asof} · 30-day price change {item.change_30d_pct:+.1f}%')
            st.write(f'**Assessment: {status}**')
            # Summaries deliberately avoid repeating lengthy technical LLM paragraphs.
            explanation = r.get('rationale') or decision.get('thesis') or item.rationale
            short_explanation = explanation.split('. ')[0].strip()
            if len(short_explanation) > 250:
                short_explanation = short_explanation[:247].rsplit(' ', 1)[0] + '…'
            st.write('**Why it stands out:**', short_explanation)
            st.write('**Main concern:**', str(risks[0]) if risks else
                     'Financial statements, market news, or price recovery evidence may be incomplete.')
            st.write('**Next step:**', str(checks[0]) if checks else
                     'Verify recent financial reports and news before considering a purchase.')
            with st.expander('View detailed research'):
                st.write('**AI research explanation:**',
                         r.get('rationale') or decision.get('thesis') or item.rationale)
                st.write('**Screen score:**', f'{item.score:.1f}/100 (not a probability of success)')
                if q:
                    st.write('**Financial health status:**', q.get('status', 'Unverified'))
                    st.write('**Summary data completeness:**',
                             f"{q.get('coverage_pct', 0):.0f}% of tracked fields; not verified financial evidence")
                    if q.get('missing'): st.write('**Missing information:**', '; '.join(q['missing']))
                sec = st.session_state.get('sec_reports', {}).get(item.ticker, {})
                if sec.get('status') == 'available':
                    st.write('**SEC EDGAR filing evidence:**')
                    for filing in sec.get('filings', []):
                        st.markdown(f"[{filing['form']} filed {filing['filed']}]({filing['url']})")
                    st.caption('Latest SEC reporting period: ' + str(sec.get('latest_reporting_period') or 'Unknown'))
                    if sec.get('missing_facts'):
                        st.warning('Not shown because no sufficiently recent comparable SEC tag was found: ' + ', '.join(sec['missing_facts']))
                    for label, fact in sec.get('facts', {}).items():
                        st.write(f"{label.replace('_',' ').title()}: ${fact['value_usd']:,.0f} "
                                 f"(period {fact.get('period_start') or 'instant'} to {fact.get('period_end')}; filed {fact['filed']})")
                    st.caption('Facts outside the latest filing period window are omitted, not treated as zero. Duration facts may be quarterly or annual and must not be compared without checking their dates. This is not full filing verification.')
                else:
                    st.caption('SEC filing evidence not available in this run. Set SEC_USER_AGENT in .env to enable it.')
                if risks: st.write('**Other risks:**', '; '.join(str(x) for x in risks))
    missing_bands = [band for band, item in selected.items() if item is None]
    if missing_bands:
        st.caption('Unfilled research slots: ' + ', '.join(missing_bands))
    st.caption('Research only. Prices and financial summaries may be stale or incomplete. '
               'AI analysis does not confirm a bottom, estimate fair value, or place trades.')
    st.stop()

st.subheader('Phase 5 · Investment committee comparison')
st.caption('Compares the completed specialist reports; it does not establish fair value or guarantee a market bottom.')
if ai_mode == 'Advanced AI Research' and len(completed_reports) >= 2:
    if st.button('Compare reviewed stocks with investment committee', key='run_committee') and allow_paid('Advanced AI Research'):
        if not os.getenv('OPENAI_API_KEY'):
            st.error('OPENAI_API_KEY missing from .env')
        else:
            try:
                with st.spinner('Comparing candidate evidence and risks (one OpenAI call)...'):
                    st.session_state['committee_report'] = compare_candidates(completed_reports, analyzed_horizon)
            except Exception as exc:
                st.error(f'Investment committee failed: {type(exc).__name__}: {exc}')
elif ai_mode == 'Advanced AI Research':
    st.info('Run six-agent reviews for at least two of the selected stocks to enable a comparison.')
committee = st.session_state.get('committee_report')
if committee:
    st.markdown('**Committee assessment (research prioritization, not a buy order)**')
    st.write(committee['summary'])
    for position in committee['rankings']:
        with st.expander(f"#{position['rank']} · {position['ticker']} · {position['stance']}", expanded=False):
            st.write(position['rationale'])
            st.write('**Key risks:**', *position['risks'])
            st.write('**Before considering an entry:**', *position['entry_conditions'])
    st.warning(committee['limitations'])
    st.download_button('Download committee JSON', __import__('json').dumps(committee, indent=2),
                       'investment_committee.json', 'application/json', key='export_committee')

st.subheader('Individual stock research')
st.caption('Expand one stock at a time to read its complete evidence and specialist reports at full width.')
for band, item in selected.items():
    title = f'{item.ticker} · ${item.price:.2f} · {band}' if item else f'{band} · No finalist'
    with st.expander(title, expanded=False):
        st.markdown(f'#### {band}')
        if item:
            st.metric(item.ticker, f'${item.price:.2f}', f'{item.change_30d_pct:+.1f}% / 30d')
            st.write(f'**Screen score:** {item.score:.1f}/100')
            st.caption(f'Data date: {item.asof}')
            st.write(item.rationale)
            if st.session_state.get('quality_mode'):
                q = st.session_state.get('quality_reports',{}).get(item.ticker)
                if q:
                    st.markdown(f"**Quality gate:** {q['status']} · {q['quality_points']}/100 points · {q['coverage_pct']:.0f}% evidence coverage")
                    st.write('**Potential value traps:**', ', '.join(q['flags']) or 'No triggered flags (not a guarantee)')
                    st.write('**Unverified or missing:**', ', '.join(q['missing']) or 'None of the tracked summary fields')
                    with st.expander('Phase 7 financial metrics, technical signals & sources'):
                        st.caption(q['source']+' · Retrieved '+q['retrieved_at'])
                        st.caption(q.get('sector_model','')); st.json(q['metrics']); st.json(q['technical'])
                        st.dataframe(pd.DataFrame(q['checks']), hide_index=True)
                    if st.button(f'Exploratory historical test: {item.ticker}',key=f'backtest_button_{item.ticker}'):
                        from quality import exploratory_backtest
                        try:
                            with st.spinner('Downloading historical prices...'):
                                close = load_prices(item.ticker)
                                st.session_state[f'backtest_result_{item.ticker}'] = exploratory_backtest(close, HORIZONS[analyzed_horizon]) if close is not None else {'status':'Price history unavailable'}
                        except Exception as exc:
                            st.error(f'Backtest unavailable: {type(exc).__name__}: {exc}')
                    backtest = st.session_state.get(f'backtest_result_{item.ticker}')
                    if backtest:
                        st.json(backtest)
                        st.caption('Historical results do not predict future performance. Current-index membership creates survivorship bias.')
            if use_ai:
                with st.expander('Budget AI research checklist (optional)'):
                    st.caption('One manual request per stock, up to 350 output tokens; cached for 7 days. Repeated clicks may be free if the inputs have not changed.')
                    if st.button(f'Analyze {item.ticker} with AI Research', key=f'budget_{item.ticker}') and allow_paid('AI Research'):
                        st.session_state[f'budget_result_{item.ticker}'] = ai_commentary(item)
                    if st.session_state.get(f'budget_result_{item.ticker}'):
                        st.write(st.session_state[f'budget_result_{item.ticker}'])
            if multi_enabled:
                if st.button(f'Run 6-agent review: {item.ticker}', key=f'review_button_{item.ticker}') and allow_paid('Advanced AI Research'):
                    if not os.getenv('OPENAI_API_KEY'):
                        st.error('OPENAI_API_KEY missing. Add it to .env in the project directory.')
                    else:
                        try:
                            from multi_agents import run_research
                            with st.spinner(f'Running specialist reviews for {item.ticker} (six model calls)...'):
                                st.session_state[f'multi_{item.ticker}'] = run_research(item, quality_report=st.session_state.get('quality_reports', {}).get(item.ticker), sec_report=st.session_state.get('sec_reports', {}).get(item.ticker))
                                st.session_state.pop('committee_report', None)
                        except Exception as exc:
                            st.error(f'Multi-agent review failed: {type(exc).__name__}: {exc}')
                report = st.session_state.get(f'multi_{item.ticker}')
                if report:
                    with st.expander(f'Phase 3 research: {item.ticker}', expanded=True):
                        decision = report['decision']
                        st.subheader(f"Verdict: {decision['status']}")
                        st.write(decision['thesis'])
                        st.caption(f"Confidence: {decision['confidence']} · {report['asof']}")
                        st.warning(decision['bottom_claim'])
                        for title, key in [('Supporting reasons','reasons'),('Risks','risks'),('Invalidation triggers','invalidation_triggers'),('Further checks','additional_checks')]:
                            st.markdown('**'+title+'**')
                            for value in decision[key]: st.write('• '+value)
                        for role, details in report['specialists'].items():
                            with st.expander(role+' agent'):
                                st.json(details)
                        st.caption(report['limitations'])
                        st.json(report['evidence']['fundamentals'])
                        for n in report['evidence']['news']:
                            st.markdown(f"- [{n['title']}]({n['url']}) — {n['published']}")
                        st.download_button('Download review JSON', __import__('json').dumps(report,indent=2),
                                           f"{item.ticker}_phase3.json", 'application/json', key=f'export_{item.ticker}')
            if research_enabled:
                if st.button(f'Research {item.ticker}', key=f'research_{item.ticker}'):
                    with st.spinner(f'Gathering evidence for {item.ticker}...'):
                        evidence=gather_evidence(item.ticker)
                        st.session_state[f'evidence_{item.ticker}']=evidence
                    if not os.getenv('OPENAI_API_KEY'):
                        st.warning('OPENAI_API_KEY missing; displaying evidence without AI analysis.')
                    else:
                        try:
                            st.session_state[f'assessment_{item.ticker}']=analyze(item,evidence)
                        except Exception as exc:
                            st.error(f'AI research unavailable: {type(exc).__name__}: {exc}')
                evidence=st.session_state.get(f'evidence_{item.ticker}')
                if evidence:
                    with st.expander(f'Phase 2 evidence for {item.ticker}',expanded=True):
                        st.caption(f"Retrieved: {evidence['retrieved_at']} · {evidence['data_source']}")
                        st.json(evidence['fundamentals'])
                        for n in evidence['news']:
                            st.markdown(f"- [{n['title']}]({n['url']}) — {n['published']}")
                        for warning in evidence['warnings']: st.warning(warning)
                        assessment=st.session_state.get(f'assessment_{item.ticker}')
                        if assessment:
                            for heading,field in [('News','news_assessment'),('Fundamentals','fundamentals_assessment'),('Industry','industry_assessment'),('Bull case','bull_case'),('Bear case','bear_case'),('Verdict','research_verdict')]:
                                st.markdown(f'**{heading}:** {assessment[field]}')
                            st.write('Missing information:',assessment['missing_information'])
                            st.write('Evidence links used:',assessment['sources_used'])

        else:
            st.info('No eligible declining stock found in this price range.')
if found:
    table=pd.DataFrame([vars(c) for c in sorted(found,key=lambda x:x.score,reverse=True)])
    st.subheader('All screened candidates')
    st.dataframe(table,hide_index=True,use_container_width=True)
    st.download_button('Download research CSV',table.to_csv(index=False).encode('utf-8'),'stock_screen.csv','text/csv')
if errors and isinstance(errors, dict) and errors.get('data_unavailable'):
    st.warning('Unavailable / failed downloads: '+', '.join(errors['data_unavailable']))
st.markdown('---')
st.markdown('**Research limitations:** Phase 11 optionally retrieves selected SEC filing metadata and tagged facts, but does not read or validate full filings. Phase 7 uses unverified Yahoo Finance summary metrics, sector-dependent heuristics and single-ticker illustrative backtests; it does not validate SEC filings or calculate intrinsic fair value. A high score is NOT a buy recommendation. The S&P 500 universe is not the entire U.S. stock market; the price filter excludes stocks above $100, and the heuristic can miss good investments or favor value traps. API data can be stale, missing or rate-limited. AI decisions are research opinions, not verified buy signals.  Phase 2 uses third-party summary fundamentals and news headlines only. It does not verify filings, read full articles, establish intrinsic value, or backtest returns. Numeric rankings are unchanged. No trades are placed.')
