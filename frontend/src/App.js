import React, { useEffect, useState } from 'react';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import '@fullcalendar/core/locales-all';

import './App.css';
import axios from 'axios';
axios.defaults.withCredentials = true;


function App() {
  const [events, setEvents] = useState([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [showRegisterForm, setShowRegisterForm] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const fetchAppointments = () => {
    axios.get('/appointments') .then((res) => {
      setEvents(res.data.map(e => ({
        ...e,
        title: e.mine ? 'Twoja wizyta' : 'Zajęte',
        color: e.mine ? '#4caf50' : '#f44336',
      })));
    });
  };

  useEffect(() => {
    axios.get('/check').then(res => {
      setLoggedIn(res.data.loggedIn);
      setIsAdmin(res.data.isAdmin);
      if (res.data.loggedIn) fetchAppointments();
    });
  }, []);

  const handleDateSelect = (selectInfo) => {
    if (!loggedIn) {
      alert("Zaloguj się, aby umówić wizytę");
      return;
    }
    if (selectInfo.allDay) return;

    const defaultDateTime = selectInfo.startStr.slice(0, 16);
    const input = prompt("Potwierdź termin (YYYY-MM-DDTHH:MM):", defaultDateTime);
    if (!input) return;

    const now = new Date();
    if (new Date(input) < now) {
      alert("Nie można umówić wizyty w przeszłości");
      return;
    }

    axios.post('/appointments', {
      start: input
    }).then(() => fetchAppointments())
      .catch((err) => alert(err.response?.data?.error || 'Błąd rejestracji'));
  };

  const handleEventClick = (clickInfo) => {
    if (!isAdmin) return;

    const choice = window.prompt(
      `Wpisz nową datę i godzinę (YYYY-MM-DDTHH:MM) lub zostaw puste, by usunąć wizytę:`,
      clickInfo.event.startStr.slice(0, 16)
    );

    if (choice === null) return;

    if (choice === '') {
      const confirmed = window.confirm(`Czy na pewno chcesz usunąć wizytę z ${clickInfo.event.startStr}?`);
      if (confirmed) {
        axios.delete(`https://kalendarz-projekt.onrender.com/appointments/${clickInfo.event.id}`)
          .then(() => fetchAppointments())
          .catch(() => alert("Błąd przy usuwaniu wizyty"));
      }
    } else {
      axios.put(`https://kalendarz-projekt.onrender.com/appointments/${clickInfo.event.id}`, {
        start: choice
      })
      .then(() => fetchAppointments())
      .catch(() => alert("Błąd przy zmianie terminu wizyty"));
    }
  };

  const register = () => {
    axios.post('https://kalendarz-projekt.onrender.com/register', {
      username,
      password,
      first_name: firstName,
      last_name: lastName,
      email,
      phone
    }).then(() => {
      alert("Zarejestrowano");
      setShowRegisterForm(false);
    }).catch((err) => {
      alert(err.response?.data?.error || "Błąd rejestracji");
    });
  };

  const login = () => {
    axios.post('https://kalendarz-projekt.onrender.com/login', { username, password })
      .then(() => {
        setLoggedIn(true);
        setUsername('');
        setPassword('');
        axios.get('https://kalendarz-projekt.onrender.com/check').then(res => {
          setIsAdmin(res.data.isAdmin);
          fetchAppointments();
        });
      })
      .catch(() => alert("Błędne dane logowania"));
  };

  const logout = () => {
    axios.post('https://kalendarz-projekt.onrender.com/logout').then(() => {
      setLoggedIn(false);
      setEvents([]);
      setIsAdmin(false);
    });
  };

  const isMobile = window.innerWidth < 768;

  return (
    <div className="App" style={{ padding: '1rem', fontFamily: 'Arial' }}>
      <h1 style={{ textAlign: 'center' }}>Kalendarz Wizyt</h1>

      {!loggedIn ? (
        <div style={{ display: 'flex', flexDirection: 'column', maxWidth: 300, margin: '0 auto' }}>
          {!showRegisterForm ? (
            <>
              <input placeholder="Login" value={username} onChange={e => setUsername(e.target.value)} />
              <input placeholder="Hasło" type="password" value={password} onChange={e => setPassword(e.target.value)} />
              <button onClick={login} style={{ marginTop: 10 }}>Zaloguj</button>
              <button onClick={() => setShowRegisterForm(true)} style={{ marginTop: 5 }}>Zarejestruj</button>
            </>
          ) : (
            <>
              <input placeholder="Imię" value={firstName} onChange={e => setFirstName(e.target.value)} />
              <input placeholder="Nazwisko" value={lastName} onChange={e => setLastName(e.target.value)} />
              <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
              <input placeholder="Telefon" value={phone} onChange={e => setPhone(e.target.value)} />
              <input placeholder="Login" value={username} onChange={e => setUsername(e.target.value)} />
              <input placeholder="Hasło" type="password" value={password} onChange={e => setPassword(e.target.value)} />
              <button onClick={register} style={{ marginTop: 10 }}>Zarejestruj</button>
              <button onClick={() => setShowRegisterForm(false)} style={{ marginTop: 5 }}>Wróć</button>
            </>
          )}
        </div>
      ) : (
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <span>Zalogowano jako: {username} {isAdmin && "(Admin)"}</span>
          <button onClick={logout} style={{ marginLeft: 10 }}>Wyloguj</button>
        </div>
      )}

      <div>
        <FullCalendar
          locale='pl'
          plugins={[timeGridPlugin, dayGridPlugin, interactionPlugin]}
          initialView={isMobile ? 'timeGridDay' : 'timeGridWeek'}
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
          }}
          selectable={true}
          events={events}
          select={handleDateSelect}
          eventClick={handleEventClick}
          dateClick={(info) => {
            if (!loggedIn) {
              alert("Zaloguj się, aby umówić wizytę");
              return;
            }
            const calendarApi = info.view.calendar;
            calendarApi.changeView('timeGridDay', info.dateStr);
          }}
          allDaySlot={false}
          selectAllow={(selectInfo) => !selectInfo.allDay}
          slotMinTime="08:00:00"
          slotMaxTime="18:00:00"
          height="auto"
        />
      </div>
    </div>
  );
}

export default App;
