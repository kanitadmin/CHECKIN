/**
 * CSRF Debug Helper
 * Add this script to debug CSRF token issues
 */

(function() {
    'use strict';
    
    console.log('🔍 CSRF Debug Helper loaded');
    
    // Function to check CSRF token availability
    function checkCSRFToken() {
        console.log('🔍 Checking CSRF token availability...');
        
        // Check meta tag
        const metaTag = document.querySelector('meta[name=csrf-token]');
        if (metaTag) {
            const token = metaTag.getAttribute('content');
            if (token && token.trim() !== '') {
                console.log('✅ CSRF token found in meta tag:', token.substring(0, 20) + '...');
                return token;
            } else {
                console.log('❌ CSRF meta tag exists but is empty');
            }
        } else {
            console.log('❌ CSRF meta tag not found');
        }
        
        // Check hidden input
        const hiddenInput = document.querySelector('input[name=csrf_token]');
        if (hiddenInput) {
            const token = hiddenInput.value;
            if (token && token.trim() !== '') {
                console.log('✅ CSRF token found in hidden input:', token.substring(0, 20) + '...');
                return token;
            } else {
                console.log('❌ CSRF hidden input exists but is empty');
            }
        } else {
            console.log('❌ CSRF hidden input not found');
        }
        
        // Additional debugging
        console.log('🔍 Available meta tags:');
        document.querySelectorAll('meta').forEach(meta => {
            const name = meta.getAttribute('name');
            const content = meta.getAttribute('content');
            if (name) {
                console.log(`  - ${name}: ${content ? content.substring(0, 30) + '...' : 'empty'}`);
            }
        });
        
        return null;
    }
    
    // Function to test CSRF token
    function testCSRFToken() {
        const token = checkCSRFToken();
        
        if (!token) {
            console.log('❌ No CSRF token available for testing');
            return;
        }
        
        console.log('🧪 Testing CSRF token with a dummy request...');
        
        // Test with a HEAD request to check-in endpoint
        fetch('/check-in', {
            method: 'HEAD',
            headers: {
                'X-CSRFToken': token
            }
        })
        .then(response => {
            console.log('🧪 CSRF test response status:', response.status);
            if (response.status === 401) {
                console.log('ℹ️ Authentication required (expected for logged-out users)');
            } else if (response.status === 403) {
                console.log('❌ CSRF token rejected');
            } else {
                console.log('✅ CSRF token accepted');
            }
        })
        .catch(error => {
            console.log('❌ CSRF test failed:', error);
        });
    }
    
    // Function to add debug info to page
    function addDebugInfo() {
        const debugDiv = document.createElement('div');
        debugDiv.id = 'csrf-debug';
        debugDiv.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: #f0f0f0;
            border: 1px solid #ccc;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            z-index: 9999;
            max-width: 300px;
        `;
        
        const token = checkCSRFToken();
        debugDiv.innerHTML = `
            <strong>CSRF Debug</strong><br>
            Token: ${token ? '✅ Found' : '❌ Missing'}<br>
            ${token ? `Value: ${token.substring(0, 20)}...` : ''}<br>
            <button onclick="window.csrfDebug.test()" style="margin-top: 5px;">Test Token</button>
            <button onclick="window.csrfDebug.hide()" style="margin-top: 5px; margin-left: 5px;">Hide</button>
        `;
        
        document.body.appendChild(debugDiv);
    }
    
    // Expose functions globally for debugging
    window.csrfDebug = {
        check: checkCSRFToken,
        test: testCSRFToken,
        show: addDebugInfo,
        hide: function() {
            const debugDiv = document.getElementById('csrf-debug');
            if (debugDiv) {
                debugDiv.remove();
            }
        }
    };
    
    // Auto-run checks when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(function() {
                checkCSRFToken();
                console.log('💡 Use window.csrfDebug.show() to display debug info');
                console.log('💡 Use window.csrfDebug.test() to test the token');
            }, 100);
        });
    } else {
        setTimeout(function() {
            checkCSRFToken();
            console.log('💡 Use window.csrfDebug.show() to display debug info');
            console.log('💡 Use window.csrfDebug.test() to test the token');
        }, 100);
    }
    
})();