DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Usage Events Investigator</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-gray-100 p-8">
    <div id="root"></div>
    <script>
        const mockEvents = Array.from({ length: 100 }, (_, i) => ({
            id: `evt_${1000 + i}`,
            timestamp: new Date(Date.now() - i * 3600000).toISOString(),
            service: ['auth', 'billing', 'gateway'][i % 3],
            status: [200, 429, 500][i % 3],
            duration: Math.floor(Math.random() * 500) + 20
        }));

        function App() {
            const [filter, setFilter] = React.useState(() => new URLSearchParams(window.location.search).get('service') || 'all');
            const [selectedEvent, setSelectedEvent] = React.useState(null);

            React.useEffect(() => {
                const params = new URLSearchParams(window.location.search);
                if (filter === 'all') params.delete('service');
                else params.set('service', filter);
                window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`);
            }, [filter]);

            const filteredData = mockEvents.filter(e => filter === 'all' || e.service === filter);

            return React.createElement('div', { className: 'space-y-6' },
                React.createElement('h1', { className: 'text-3xl font-bold border-b border-gray-700 pb-4' }, '🔍 On-Call Incident Investigator'),
                React.createElement('div', { className: 'flex gap-4 items-center' },
                    React.createElement('label', { className: 'font-medium' }, 'Filter by Service:'),
                    React.createElement('select', {
                        value: filter,
                        onChange: (e) => setFilter(e.target.value),
                        className: 'bg-gray-800 border border-gray-700 rounded p-2 text-white'
                    },
                        React.createElement('option', { value: 'all' }, 'All Services'),
                        React.createElement('option', { value: 'auth' }, 'Auth Service'),
                        React.createElement('option', { value: 'billing' }, 'Billing Service'),
                        React.createElement('option', { value: 'gateway' }, 'API Gateway')
                    )
                ),
                React.createElement('div', { className: 'grid grid-cols-3 gap-6' },
                    React.createElement('div', { className: 'col-span-2 bg-gray-800 p-4 rounded shadow overflow-x-auto' },
                        React.createElement('table', { className: 'w-full text-left' },
                            React.createElement('thead', { className: 'bg-gray-700' },
                                React.createElement('tr', null,
                                    React.createElement('th', { className: 'p-3' }, 'Event ID'),
                                    React.createElement('th', { className: 'p-3' }, 'Service'),
                                    React.createElement('th', { className: 'p-3' }, 'Status'),
                                    React.createElement('th', { className: 'p-3' }, 'Duration (ms)')
                                )
                            ),
                            React.createElement('tbody', null,
                                filteredData.slice(0, 10).map(e => 
                                    React.createElement('tr', {
                                        key: e.id,
                                        onClick: () => setSelectedEvent(e),
                                        className: 'border-b border-gray-700 hover:bg-gray-700 cursor-pointer'
                                    },
                                        React.createElement('td', { className: 'p-3' }, e.id),
                                        React.createElement('td', { className: 'p-3' }, e.service),
                                        React.createElement('td', { className: 'p-3' }, e.status),
                                        React.createElement('td', { className: 'p-3' }, `${e.duration}ms`)
                                    )
                                )
                            )
                        )
                    ),
                    React.createElement('div', { className: 'bg-gray-800 p-4 rounded shadow' },
                        React.createElement('h3', { className: 'text-xl font-bold mb-4' }, 'Selected Event Inspection'),
                        selectedEvent ? React.createElement('pre', { className: 'bg-gray-900 p-4 rounded text-sm overflow-auto text-green-400' }, 
                            JSON.stringify(selectedEvent, null, 2)
                        ) : React.createElement('p', { className: 'text-gray-400' }, 'Click a row in the system log table to inspect details.')
                    )
                )
            );
        }

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(React.createElement(App));
    </script>
</body>
</html>
"""
