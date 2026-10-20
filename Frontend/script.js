const searchForm = document.querySelector(".search-box");
const searchInput = document.querySelector(".search-wrapper input");
const dateBlocks = document.getElementById("Date-Blocks");
const overallRating = document.querySelector("#line h1:first-child");
const ratingMessage = document.querySelector("#line h1:last-child");

const factors = ["pressure", "temperature", "clouds", "rain", "surf"];

let forecastDays = [];
let selectedDay = 0;

function clamp(value) {
    return Math.max(0, Math.min(10, value));
}

function calculateBiteScore(day) {
    const temp = day.temperature;
    const rain = day.rain;
    const clouds = day.clouds;
    const pressure = day.pressure;
    const wind = day.wind;

    const scores = {
        pressure: clamp(10 - Math.abs(pressure - 1013) / 5),
        temperature: clamp(10 - Math.abs(temp - 20) / 3),
        clouds: clamp(10 - Math.abs(clouds - 60) / 12),
        rain: clamp(10 - rain * 2),
        surf: clamp(10 - wind / 5)
    };

    const overall = (
        scores.pressure * 0.25 +
        scores.temperature * 0.25 +
        scores.clouds * 0.20 +
        scores.rain * 0.15 +
        scores.surf * 0.15
    );

    return {
        score: Math.max(1, Math.round(overall)),
        factors: scores
    };
}

function getScoreColor(score) {
    const colors = {
        1: "#dc2626",
        2: "#ea380c",
        3: "#ea990c",
        4: "#ecda14",
        5: "#e9ec14",
        6: "#b4ff29",
        7: "#84a40c",
        8: "#65a30d",
        9: "#10b64d",
        10: "#16a34a"
    };

    return colors[score];
}

function getRatingMessage(score) {
    if (score >= 9) return "Excellent day to fish!";
    if (score >= 7) return "Great day to fish";
    if (score >= 5) return "Decent day to fish";
    if (score >= 3) return "Poor fishing conditions";
    return "Not a good day to fish";
}

async function getCoordinates(city) {
    const url =
        `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=10&countryCode=US&format=json`;

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error("Unable to search for city");
    }

    const data = await response.json();

    if (!data.results || data.results.length === 0) {
        throw new Error("City not found");
    }

    const californiaCity = data.results.find(
        location => location.admin1 === "California"
    );

    if (!californiaCity) {
        throw new Error("Please enter a city in California");
    }

    return californiaCity;
}

async function getWeather(latitude, longitude) {
    const url =
        `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}` +
        `&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max` +
        `&hourly=surface_pressure,cloud_cover` +
        `&temperature_unit=celsius&wind_speed_unit=kmh` +
        `&timezone=auto&forecast_days=7`;

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error("Unable to retrieve weather data");
    }

    const data = await response.json();

    if (!data.daily || !data.hourly) {
        throw new Error("Weather data unavailable");
    }

    return data;
}

function processForecast(data) {
    return data.daily.time.map((date, index) => {
        const hourlyIndices = data.hourly.time
            .map((time, i) => time.startsWith(date) ? i : -1)
            .filter(i => i !== -1);

        const average = (values) => {
            const valid = values.filter(Number.isFinite);
            return valid.length
                ? valid.reduce((sum, value) => sum + value, 0) / valid.length
                : 0;
        };

        const day = {
            date,
            temperature: (
                data.daily.temperature_2m_max[index] +
                data.daily.temperature_2m_min[index]
            ) / 2,
            rain: data.daily.precipitation_sum[index] ?? 0,
            wind: data.daily.wind_speed_10m_max[index] ?? 0,
            pressure: average(
                hourlyIndices.map(i => data.hourly.surface_pressure[i])
            ),
            clouds: average(
                hourlyIndices.map(i => data.hourly.cloud_cover[i])
            )
        };

        return {
            ...day,
            ...calculateBiteScore(day)
        };
    });
}

function displayForecast() {
    dateBlocks.innerHTML = "";

    forecastDays.forEach((day, index) => {
        const date = new Date(day.date + "T12:00:00");

        const formattedDate = date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric"
        });

        const dayElement = document.createElement("div");
        dayElement.className = "day";

        if (index === selectedDay) {
            dayElement.id = "today";
        }

        dayElement.innerHTML = `
            <h1 class="date">${formattedDate}</h1>
            <span class="score" style="color: ${getScoreColor(day.score)}">
                ${day.score}
            </span>
        `;

        dayElement.addEventListener("click", () => {
            selectedDay = index;
            displayForecast();
            updateMainRating(index);
        });

        dateBlocks.appendChild(dayElement);
    });
}

function updateMainRating(index) {
    const day = forecastDays[index];

    overallRating.textContent = `${day.score}/10`;
    overallRating.style.color = getScoreColor(day.score);

    ratingMessage.textContent = getRatingMessage(day.score);

    factors.forEach(factor => {
        const bar = document.getElementById(factor);

        if (!bar) return;

        const score = day.factors[factor];

        bar.style.width = `${score * 10}%`;
        bar.style.backgroundColor = getScoreColor(
            Math.max(1, Math.round(score))
        );
    });
}

async function searchCity(city) {
    const button = searchForm.querySelector("button");

    try {
        button.disabled = true;
        button.textContent = "Loading...";

        const location = await getCoordinates(city);
        const weather = await getWeather(
            location.latitude,
            location.longitude
        );

        forecastDays = processForecast(weather);
        selectedDay = 0;

        displayForecast();
        updateMainRating(0);

        searchInput.value = location.name;

    } catch (error) {
        alert(error.message);
        console.error(error);
    } finally {
        button.disabled = false;
        button.textContent = "Search";
    }
}

searchForm.addEventListener("submit", event => {
    event.preventDefault();

    const city = searchInput.value.trim();

    if (!city) {
        alert("Please enter a city");
        return;
    }

    searchCity(city);
});

searchCity("Los Angeles");

const toggleColorMode = (e) => {
  // Switch to Light Mode
  if (e.currentTarget.classList.contains("light--hidden")) {
    // Sets the custom HTML attribute
    document.documentElement.setAttribute("color-mode", "light");

    //Sets the user's preference in local storage
    localStorage.setItem("color-mode", "light");
    return;
  }

  /* Switch to Dark Mode
    Sets the custom HTML attribute */
  document.documentElement.setAttribute("color-mode", "dark");

  // Sets the user's preference in local storage
  localStorage.setItem("color-mode", "dark");
};

// Get the buttons in the DOM
const toggleColorButtons = document.querySelectorAll(".color-mode__btn");

// Set up event listeners
toggleColorButtons.forEach((btn) => {
  btn.addEventListener("click", toggleColorMode);
});
