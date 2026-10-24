"""Optional real-Chrome end-to-end check; isolated demo artifacts, DB and profile."""
import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from threading import Thread
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
import websocket
from werkzeug.serving import make_server
from src.api.app import create_app
from src.models.demo import load_demo_artifacts


class Browser:
    def __init__(self, url):
        self.socket = websocket.create_connection(url, timeout=20, origin='http://localhost')
        self.sequence = 0
        self.errors = []

    def call(self, method, params=None):
        self.sequence += 1
        identifier = self.sequence
        self.socket.send(json.dumps({'id': identifier, 'method': method, 'params': params or {}}))
        while True:
            data = json.loads(self.socket.recv())
            if data.get('method') == 'Runtime.exceptionThrown':
                self.errors.append(data['params'])
            if data.get('id') == identifier:
                if 'error' in data:
                    raise AssertionError(data['error'])
                return data.get('result', {})

    def js(self, expression):
        result = self.call('Runtime.evaluate', {'expression':expression,'returnByValue':True,'awaitPromise':True,'userGesture':True})
        if 'exceptionDetails' in result:
            raise AssertionError(result['exceptionDetails'])
        return result.get('result', {}).get('value')

    def until(self, expression):
        deadline = time.monotonic()+40
        while time.monotonic()<deadline:
            if self.js(expression):
                return
            time.sleep(.15)
        raise AssertionError('Browser condition timed out: '+expression)

    def capture(self, output):
        metrics=self.call('Page.getLayoutMetrics')['cssContentSize']
        screenshot=self.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':True,
            'clip':{'x':0,'y':0,'width':self.js('document.documentElement.clientWidth'),'height':metrics['height'],'scale':1}})
        output.write_bytes(base64.b64decode(screenshot['data']))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='/private/tmp/sentinelnids-browser')
    args=parser.parse_args()
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    chrome=os.environ.get('NIDS_CHROME_BINARY') or shutil.which('google-chrome') or shutil.which('chromium')
    mac=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    if not chrome and mac.exists():chrome=str(mac)
    if not chrome:parser.exit(1,'Chrome/Chromium missing. Set NIDS_CHROME_BINARY.\n')
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        with patch.dict(os.environ,{'NIDS_DEMO_MODEL_DIR':str(root/'model')}):
            load_demo_artifacts.cache_clear()
            server=make_server('127.0.0.1',0,create_app(root/'alerts.db'))
            thread=Thread(target=server.serve_forever,daemon=True);thread.start()
            browser=None;process=None
            try:
                process=subprocess.Popen([chrome,'--headless','--disable-gpu','--no-first-run','--no-default-browser-check',
                    '--remote-debugging-port=0','--remote-allow-origins=*',f'--user-data-dir={root / "chrome"}','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                active=root/'chrome/DevToolsActivePort'
                deadline=time.monotonic()+30
                while not active.exists():
                    if time.monotonic()>deadline:raise AssertionError('Chrome did not start')
                    time.sleep(.1)
                debug=f'http://127.0.0.1:{active.read_text().splitlines()[0]}'
                target=next(item for item in requests.get(debug+'/json',timeout=10).json() if item['type']=='page')
                browser=Browser(target['webSocketDebuggerUrl'])
                browser.call('Runtime.enable');browser.call('Page.enable')
                browser.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
                base=f'http://127.0.0.1:{server.server_port}'
                browser.call('Page.navigate',{'url':base})
                browser.until("document.getElementById('kpi-total')?.textContent === '0' && !!window.Chart")
                assert browser.js("!document.getElementById('empty-state').hidden")
                assert browser.js("document.getElementById('status-api').textContent === 'Online'")
                browser.js("document.querySelector('[data-scenario=benign]').click()")
                browser.until("document.getElementById('demo-result').textContent.includes('Benign verdict') && !document.querySelector('[data-scenario=benign]').disabled")
                assert browser.js("document.getElementById('kpi-total').textContent === '0'")
                for index,name in enumerate(['port_scan','brute_force','dos'],1):
                    browser.js(f"document.querySelector('[data-scenario={name}]').click()")
                    browser.until(f"document.getElementById('kpi-total').textContent === '{index}' && !document.querySelector('[data-scenario={name}]').disabled")
                assert browser.js("document.getElementById('kpi-high').textContent === '1' && document.getElementById('kpi-medium').textContent === '2'")
                assert browser.js("document.querySelectorAll('#alerts-body tr').length === 3")
                assert browser.js("Chart.getChart('category-chart').data.datasets[0].data.reduce((a,b)=>a+b,0) === 3")
                assert browser.js("Chart.getChart('timeline-chart').data.datasets[0].data.reduce((a,b)=>a+b,0) === 3")
                assert browser.js("document.getElementById('status-mode').textContent === 'DEMO MODE' && document.getElementById('mode-title').textContent === 'DEMO MODE'")
                assert browser.js("document.querySelectorAll('svg use[href*=lucide]').length >= 15")
                assert browser.js("document.querySelector('.brand-icon svg').getBBox().width > 0"), 'Lucide geometry did not render'
                browser.js("document.querySelector('#alerts-body button').click()")
                browser.until("document.getElementById('detail-content').textContent.includes('Risk:')")
                assert browser.js("document.getElementById('alert-dialog').open && document.getElementById('detail-content').textContent.includes('DEMO / SIMULATED')")
                browser.js("document.getElementById('close-dialog').click()")
                browser.js("document.getElementById('filter-severity').value='High';document.getElementById('filter-severity').dispatchEvent(new Event('change'))")
                browser.until("document.querySelectorAll('#alerts-body tr').length === 1")
                browser.js("document.getElementById('filter-severity').value='';document.getElementById('filter-severity').dispatchEvent(new Event('change'))")
                browser.until("document.querySelectorAll('#alerts-body tr').length === 3")
                browser.capture(output/'desktop.png')
                browser.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
                time.sleep(.3)
                assert browser.js("document.documentElement.scrollWidth <= window.innerWidth"), 'Mobile page overflow'
                browser.capture(output/'mobile.png')
                # Polling, not a demo callback, must show an externally submitted event.
                response=requests.post(base+'/api/demo',json={'scenario':'port_scan'},timeout=30)
                response.raise_for_status()
                browser.until("document.getElementById('kpi-total').textContent === '4'")
                browser.js("document.getElementById('capture-file').value='scan_nmap_synscan.pcapng';document.getElementById('process-capture').click()")
                browser.until("document.getElementById('kpi-total').textContent === '5' && document.getElementById('capture-result').textContent.includes('2017 packets')")
                assert browser.js("document.getElementById('alerts-body').textContent.includes('OFFLINE CAPTURE / RULES')")
                browser.js("window.confirm=()=>true;document.getElementById('reset-demo').click()")
                browser.until("document.getElementById('kpi-total').textContent === '1' && document.getElementById('demo-result').textContent.includes('Cleared 4')")
                assert browser.js("document.getElementById('alerts-body').textContent.includes('OFFLINE CAPTURE / RULES')")
                # Exercise honest stale/offline state and recovery.
                server.shutdown();thread.join(timeout=5);server.server_close()
                browser.js('refreshDashboard()')
                browser.until("!document.getElementById('api-error').hidden")
                assert not browser.errors,browser.errors
                print('Browser PASS: empty state, four scenarios, real charts/KPIs, evidence, filters, Lucide SVG geometry, mobile layout, polling, reset and offline errors')
                print('Screenshots:',output)
            finally:
                if browser:browser.socket.close()
                if process:
                    process.terminate()
                    try:process.wait(timeout=10)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
                if thread.is_alive():server.shutdown();thread.join(timeout=5)
                server.server_close();load_demo_artifacts.cache_clear()


if __name__=='__main__':main()
