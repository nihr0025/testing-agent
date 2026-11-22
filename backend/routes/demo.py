from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/demo", tags=["Demo Test Website"])

@router.get("", response_class=HTMLResponse)
def get_demo_site():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acme Test Shop - Demo Automation Target</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f8fafc;
            color: #1e293b;
        }
        nav {
            background: #1e293b;
            color: white;
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        nav a { color: #38bdf8; text-decoration: none; margin-left: 16px; font-weight: 500; }
        .hero {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            color: white;
            padding: 48px 32px;
            text-align: center;
        }
        .container {
            max-width: 1000px;
            margin: 32px auto;
            padding: 0 16px;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        input, button {
            padding: 10px 14px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            font-size: 14px;
        }
        button {
            background: #0284c7;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }
        button:hover { background: #0369a1; }
        .alert {
            padding: 12px;
            border-radius: 6px;
            margin-top: 12px;
            display: none;
        }
        .alert-success { background: #dcfce7; color: #166534; }
        .alert-error { background: #fee2e2; color: #991b1b; }
    </style>
</head>
<body>
    <nav>
        <div style="font-weight: bold; font-size: 18px;">🛒 Acme Demo Shop</div>
        <div>
            <a href="#search" id="nav-search">Search</a>
            <a href="#login" id="nav-login">Login</a>
            <a href="#contact" id="nav-contact">Feedback</a>
        </div>
    </nav>

    <div class="hero">
        <h1 id="main-heading">Automated QA Sandbox Target</h1>
        <p>A reliable testbed for Playwright and Selenium Multi-Agent automation.</p>
    </div>

    <div class="container">
        <!-- Search Section -->
        <div class="card" id="search-section">
            <h2>Product Catalog Search</h2>
            <div style="display: flex; gap: 8px;">
                <input type="text" id="search-input" placeholder="Search products (e.g. laptop, phone)..." style="flex: 1;" />
                <button id="search-btn" onclick="handleSearch()">Search Catalog</button>
            </div>
            <div id="search-results" class="alert alert-success">Search query executed successfully!</div>
        </div>

        <!-- Authentication Form Section -->
        <div class="card" id="login-section">
            <h2>User Account Login</h2>
            <div style="display: flex; flex-direction: column; gap: 12px; max-width: 400px;">
                <div>
                    <label for="username" style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px;">Username / Email</label>
                    <input type="text" id="username" placeholder="testuser@example.com" style="width: 100%; box-sizing: border-box;" />
                </div>
                <div>
                    <label for="password" style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px;">Password</label>
                    <input type="password" id="password" placeholder="••••••••" style="width: 100%; box-sizing: border-box;" />
                </div>
                <button id="login-btn" onclick="handleLogin()" style="width: 100%;">Sign In</button>
            </div>
            <div id="login-alert" class="alert"></div>
        </div>
    </div>

    <script>
        function handleSearch() {
            const val = document.getElementById("search-input").value;
            const res = document.getElementById("search-results");
            res.style.display = "block";
            res.innerText = val ? 'Showing results for: "' + val + '"' : 'Showing all 12 default catalog items';
        }

        function handleLogin() {
            const user = document.getElementById("username").value.trim();
            const pass = document.getElementById("password").value.trim();
            const alert = document.getElementById("login-alert");
            alert.style.display = "block";
            if (!user || !pass) {
                alert.className = "alert alert-error";
                alert.innerText = "Error: Username and password are required.";
            } else {
                alert.className = "alert alert-success";
                alert.innerText = "Welcome back, " + user + "! Authentication successful.";
            }
        }
    </script>
</body>
</html>
"""
