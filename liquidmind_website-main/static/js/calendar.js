document.addEventListener('DOMContentLoaded', function() {
    const calendarBody = document.getElementById('calendar-body');
    const monthAndYear = document.getElementById('monthAndYear');
    const monthSelect = document.getElementById('month');
    const yearSelect = document.getElementById('year');
    let currentMonth = new Date().getMonth();
    let currentYear = new Date().getFullYear();

    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const years = [];
    for (let i = 1900; i <= 2100; i++) {
        years.push(i);
    }

    monthSelect.innerHTML = months.map((month, index) => `<option value=${index}>${month}</option>`).join('');
    yearSelect.innerHTML = years.map(year => `<option value=${year}>${year}</option>`).join('');

    function renderCalendar(month, year) {
        const firstDay = new Date(year, month).getDay();
        const daysInMonth = 32 - new Date(year, month, 32).getDate();

        calendarBody.innerHTML = '';
        monthAndYear.innerText = `${months[month]} ${year}`;

        let date = 1;
        for (let i = 0; i < 6; i++) {
            const row = document.createElement('tr');

            for (let j = 0; j < 7; j++) {
                const cell = document.createElement('td');
                if (i === 0 && j < firstDay) {
                    cell.innerText = '';
                } else if (date > daysInMonth) {
                    break;
                } else {
                    cell.innerText = date;
                    cell.classList.add('date-cell');
                    cell.dataset.date = `${year}-${String(month + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`;
                    cell.addEventListener('click', handleDateClick);
                    date++;
                }
                row.appendChild(cell);
            }

            calendarBody.appendChild(row);
        }
    }

    function handleDateClick(event) {
        const selectedDate = event.target.dataset.date;
        fetch('/calendar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ selected_date: selectedDate })
        })
        .then(response => response.json())
        .then(data => {
            alert(`Selected date is: ${data.selected_date}`);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    function previous() {
        currentYear = (currentMonth === 0) ? currentYear - 1 : currentYear;
        currentMonth = (currentMonth === 0) ? 11 : currentMonth - 1;
        renderCalendar(currentMonth, currentYear);
    }

    function next() {
        currentYear = (currentMonth === 11) ? currentYear + 1 : currentYear;
        currentMonth = (currentMonth + 1) % 12;
        renderCalendar(currentMonth, currentYear);
    }

    function jump() {
        currentYear = parseInt(yearSelect.value);
        currentMonth = parseInt(monthSelect.value);
        renderCalendar(currentMonth, currentYear);
    }

    document.getElementById('previous').addEventListener('click', previous);
    document.getElementById('next').addEventListener('click', next);
    monthSelect.addEventListener('change', jump);
    yearSelect.addEventListener('change', jump);

    renderCalendar(currentMonth, currentYear);
});
