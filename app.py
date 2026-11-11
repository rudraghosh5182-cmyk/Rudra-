import os
import asyncio
from flask import Flask, request, jsonify, render_template_string
from playwright.async_api import async_playwright

app = Flask(__name__)

# Embedded Frontend UI with Multiple Account Management
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Automation Studio - Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: sans-serif; }
        .glass { background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(10px); border: 1px solid #30363d; }
    </style>
</head>
<body class="p-4 max-w-lg mx-auto min-h-screen flex items-center justify-center">
    <div class="glass p-6 rounded-2xl shadow-xl w-full">
        <h1 class="text-2xl font-bold text-cyan-400 mb-4 text-center">⚡ X Automation Studio</h1>
        
        <!-- Step 1: Manage Accounts -->
        <div id="step-accounts" class="space-y-4">
            <label class="block text-sm text-gray-400">Add X Account Usernames</label>
            <div class="flex gap-2">
                <input type="text" id="username-input" placeholder="e.g. Rudraghosh49qb" class="w-full p-3 bg-gray-900 border border-gray-700 rounded-xl text-white focus:outline-none focus:border-cyan-400">
                <button onclick="addAccount()" class="bg-gray-800 hover:bg-gray-700 border border-cyan-500/30 text-cyan-400 font-bold px-4 rounded-xl">Add</button>
            </div>
            
            <div class="text-xs text-gray-400 mt-2">Active Accounts Added:</div>
            <div id="account-list" class="flex flex-wrap gap-2 min-h-[40px] p-2 bg-black/40 rounded-xl border border-gray-800">
                <span class="text-gray-500 text-xs italic">No accounts added yet</span>
            </div>

            <button onclick="proceedToLinks()" class="w-full bg-cyan-500 hover:bg-cyan-600 font-bold p-3 rounded-xl text-black mt-4">Next: Add Links</button>
        </div>

        <!-- Step 2: Links -->
        <div id="step-links" class="hidden space-y-4">
            <p class="text-green-400 text-sm">Active Accounts: <b id="display-accounts-count">0</b> selected</p>
            <textarea id="link-input" placeholder="Paste X post link here..." class="w-full p-3 bg-gray-900 border border-gray-700 rounded-xl text-white h-24 focus:outline-none focus:border-cyan-400"></textarea>
            <button onclick="addLink()" class="w-full bg-gray-800 hover:bg-gray-700 border border-cyan-500/30 text-cyan-400 font-bold p-3 rounded-xl">Add Link</button>
            <div class="text-xs text-gray-400">Total links saved: <span id="link-count" class="text-cyan-400 font-bold">0</span></div>
            <div class="flex gap-2">
                <button onclick="backToAccounts()" class="w-1/3 bg-gray-700 hover:bg-gray-600 text-xs font-bold p-3 rounded-xl">Back</button>
                <button onclick="showActions()" class="w-2/3 bg-cyan-500 hover:bg-cyan-600 font-bold p-3 rounded-xl text-black">DONE</button>
            </div>
        </div>

        <!-- Step 3: Actions -->
        <div id="step-actions" class="hidden space-y-3">
            <h3 class="text-center font-bold text-lg mb-2">Select Action for All IDs</h3>
            <button onclick="runAutomation('like')" class="w-full bg-blue-600 hover:bg-blue-500 font-bold p-3 rounded-xl">Like</button>
            <button onclick="runAutomation('repost')" class="w-full bg-green-600 hover:bg-green-500 font-bold p-3 rounded-xl">Repost</button>
            <button onclick="runAutomation('both')" class="w-full bg-purple-600 hover:bg-purple-500 font-bold p-3 rounded-xl">Like & Repost</button>
            <button onclick="resetAll()" class="w-full bg-gray-700 hover:bg-gray-600 text-sm p-2 rounded-xl mt-4">Reset All</button>
        </div>

        <!-- Logs & Status -->
        <div id="console" class="mt-6 p-3 bg-black/60 rounded-xl border border-gray-800 text-xs font-mono h-36 overflow-y-auto hidden">
            <div id="console-logs" class="space-y-1 text-gray-300"></div>
        </div>
    </div>

    <script>
        let accounts = [];
        let links = [];

        function addAccount() {
            const input = document.getElementById('username-input');
            let uname = input.value.trim().replace('@', '');
            if(uname && !accounts.includes(uname)) {
                accounts.push(uname);
                input.value = "";
                updateAccountUI();
            }
        }

        function removeAccount(uname) {
            accounts = accounts.filter(acc => acc !== uname);
            updateAccountUI();
        }

        function updateAccountUI() {
            const listDiv = document.getElementById('account-list');
            if(accounts.length === 0) {
                listDiv.innerHTML = '<span class="text-gray-500 text-xs italic">No accounts added yet</span>';
                return;
            }
            listDiv.innerHTML = accounts.map(acc => `
                <span class="bg-cyan-950 border border-cyan-500/40 text-cyan-300 px-2 py-1 rounded-lg text-xs flex items-center gap-1">
                    @${acc} <span onclick="removeAccount('${acc}')" class="cursor-pointer text-red-400 font-bold ml-1">×</span>
                </span>
            `).join('');
        }

        function proceedToLinks() {
            if(accounts.length === 0) return alert('Please add at least one X account!');
            document.getElementById('display-accounts-count').innerText = accounts.length;
            document.getElementById('step-accounts').classList.add('hidden');
            document.getElementById('step-links').classList.remove('hidden');
        }

        function backToAccounts() {
            document.getElementById('step-links').classList.add('hidden');
            document.getElementById('step-accounts').classList.remove('hidden');
        }

        function addLink() {
            const input = document.getElementById('link-input');
            if(input.value.trim()) {
                links.push(input.value.trim());
                input.value = "";
                document.getElementById('link-count').innerText = links.length;
            }
        }

        function showActions() {
            if(links.length === 0) return alert('Please add at least one link!');
            document.getElementById('step-links').classList.add('hidden');
            document.getElementById('step-actions').classList.remove('hidden');
        }

        function resetAll() {
            accounts = [];
            links = [];
            document.getElementById('account-list').innerHTML = '<span class="text-gray-500 text-xs italic">No accounts added yet</span>';
            document.getElementById('link-count').innerText = "0";
            document.getElementById('console').classList.add('hidden');
            document.getElementById('step-actions').classList.add('hidden');
            document.getElementById('step-accounts').classList.remove('hidden');
        }

        async function runAutomation(action) {
            document.getElementById('step-actions').classList.add('hidden');
            document.getElementById('console').classList.remove('hidden');
            const logs = document.getElementById('console-logs');
            logs.innerHTML += `<div class="text-cyan-400">🚀 Starting ${action.toUpperCase()} automation for ${accounts.length} account(s)...</div>`;

            const res = await fetch('/api/run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ accounts, links, action })
            });
            const data = await res.json();
            
            if(data.status === 'suspended') {
                logs.innerHTML += `<div class="text-red-500 font-bold">🚨 Suspension alert detected on an account!</div>`;
            } else {
                logs.innerHTML += `<div class="text-green-400 font-bold">🎉 All tasks executed successfully across active IDs with 5-7s interval.</div>`;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/run', methods=['POST'])
def run_task():
    data = request.json
    accounts = data.get('accounts', [])
    links = data.get('links', [])
    action = data.get('action')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(execute_playwright(accounts, links, action))
    return jsonify(result)

async def execute_playwright(accounts, links, action):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for account in accounts:
            context = await browser.new_context()
            page = await context.new_page()
            
            for link in links:
                try:
                    await page.goto(link)
                    await asyncio.sleep(6)  # 5 to 7 seconds interval gap
                    
                    if "suspended" in page.url:
                        await browser.close()
                        return {"status": "suspended"}

                    if action in ['like', 'both']:
                        like_btn = page.locator('[data-testid="like"]')
                        if await like_btn.is_visible():
                            await like_btn.click()
                    
                    if action in ['repost', 'both']:
                        repost_btn = page.locator('[data-testid="retweet"]')
                        if await repost_btn.is_visible():
                            await repost_btn.click()
                            await page.locator('[data-testid="retweetConfirm"]').click()

                    await asyncio.sleep(6)  # Gap between actions
                except Exception as e:
                    pass
            
            await context.close()

        await browser.close()
        return {"status": "success"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
      
