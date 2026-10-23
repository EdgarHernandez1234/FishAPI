const searchForm = document.querySelector(".search-box");
const searchInput = document.getElementById("city-search");
const searchButton = searchForm.querySelector("button");
const dateBlocks = document.getElementById("Date-Blocks");
const overallRating = document.getElementById("overall-score");
const ratingMessage = document.getElementById("rating-message");
const scoreExplanation = document.getElementById("score-explanation");

const weatherTemperature = document.getElementById("weather-temperature");
const weatherRain = document.getElementById("weather-rain");
const weatherWind = document.getElementById("weather-wind");
const weatherPressure = document.getElementById("weather-pressure");
const windDirection = document.getElementById("wind-direction");
const weatherTitle = document.getElementById("weather-title");
const weatherBadge = document.getElementById("weather-badge");
const weatherUpdated = document.getElementById("weather-updated");

const themeToggle = document.getElementById("theme-toggle");
const themeIcon = document.getElementById("theme-icon");
const themeLabel = document.getElementById("theme-label");

const bestDayName = document.getElementById("best-day-name");
const bestDayScore = document.getElementById("best-day-score");
const bestDayReason = document.getElementById("best-day-reason");
const bestDayTime = document.getElementById("best-day-time");

const fishingTimesList = document.getElementById("fishing-times-list");
const hourlyTimesList = document.getElementById("hourly-times-list");
const hourlyTitle = document.getElementById("hourly-title");
const hourlyDaySelect = document.getElementById("hourly-day-select");

const tabButtons = document.querySelectorAll(".tab-button");
const tabContents = document.querySelectorAll(".tab-content");

const communityPosts = document.getElementById("community-posts");
const postForm = document.getElementById("post-form");
const communitySearch = document.getElementById("community-search");
const communityCategory = document.getElementById("community-category");
const communitySort = document.getElementById("community-sort");

const factors = ["pressure", "temperature", "clouds", "rain", "surf", "season", "moon"];

/* ---------- backend connection (added) ---------- */

const API = "http://127.0.0.1:8000";

// bar id (from the HTML) -> factor name returned by the backend
const factorMap = {
    pressure: "pressure",
    temperature: "water_temp",
    clouds: "sky",
    rain: "precipitation",
    surf: "wind",
    season: "season",
    moon: "moon"

};

let spots = [];
let currentSpot = null;

function formatScore(score) {
    return score.toFixed(1);
}

function spotName(spot) {
    return spot.name ?? spot.id;
}

async function getSpots() {
    const response = await fetch(`${API}/api/spots`);
    if (!response.ok) throw new Error("Could not load fishing spots.");
    return response.json();
}

async function getScoreData(spotId) {
    const response = await fetch(`${API}/api/spots/${encodeURIComponent(spotId)}/score`);
    if (!response.ok) throw new Error("Could not load the fishing forecast for this spot.");
    return response.json();
}

function fillSpotList() {
    let list = document.getElementById("spot-list");

    if (!list) {
        list = document.createElement("datalist");
        list.id = "spot-list";
        searchInput.after(list);
        searchInput.setAttribute("list", "spot-list");
    }

    list.innerHTML = "";
    spots.forEach(spot => {
        const option = document.createElement("option");
        option.value = spotName(spot);
        list.appendChild(option);
    });
}

function findSpot(query) {
    const q = query.trim().toLowerCase();
    return (
        spots.find(spot => spotName(spot).toLowerCase() === q) ||
        spots.find(spot => spotName(spot).toLowerCase().includes(q)) ||
        spots.find(spot => String(spot.id).toLowerCase() === q)
    );
}

/* ---------- original code ---------- */

let forecastDays = [];
let hourlyFishingForecast = [];
let selectedDay = 0;
let currentWeather = null;
let currentCity = "Los Angeles";
let currentCoordinates = null;
let requestCounter = 0;
let weatherRequestCounter = 0;
let refreshInProgress = false;

function switchTab(tabId) {
    tabButtons.forEach(button => {
        const active = button.dataset.tab === tabId;
        button.classList.toggle("active", active);
        button.setAttribute("aria-current", active ? "page" : "false");
    });

    tabContents.forEach(content => {
        const active = content.id === tabId;
        content.classList.toggle("active", active);
        content.hidden = !active;
    });
}

tabButtons.forEach(button => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
});

function setTheme(isLight) {
    document.body.classList.toggle("light-mode", isLight);
    themeIcon.textContent = isLight ? "🌙" : "☀️";
    themeLabel.textContent = isLight ? "Dark Mode" : "Light Mode";
    themeToggle.setAttribute("aria-label", isLight ? "Switch to dark mode" : "Switch to light mode");
    themeToggle.setAttribute("aria-pressed", String(!isLight));

    try {
        localStorage.setItem("fisch-halloween-theme", isLight ? "light" : "dark");
    } catch (error) {
        console.warn(error);
    }
}

let savedTheme = "dark";

try {
    savedTheme = localStorage.getItem("fisch-halloween-theme") || "dark";
} catch (error) {
    savedTheme = "dark";
}

setTheme(savedTheme === "light");

themeToggle.addEventListener("click", () => {
    setTheme(!document.body.classList.contains("light-mode"));
});

function clamp(value) {
    return Math.max(0, Math.min(10, value));
}

function getScoreColor(score) {
    const colors = {
        1: "#ef4444", 2: "#f97316", 3: "#fb923c",
        4: "#f59e0b", 5: "#eab308", 6: "#a3e635",
        7: "#84cc16", 8: "#65a30d", 9: "#22c55e",
        10: "#16a34a"
    };

    return colors[Math.max(1, Math.min(10, Math.round(score)))];
}

function getRatingMessage(score) {
    if (score >= 9) return "🎃 A monster day to fish!";
    if (score >= 7) return "👻 Spookily good fishing!";
    if (score >= 5) return "🦇 Decent fishing conditions";
    if (score >= 3) return "🌙 The fish are hiding";
    return "💀 Beware of poor fishing conditions";
}

function getWindDirection(degrees) {
    if (!Number.isFinite(degrees)) return "Unknown";
    const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
    return directions[Math.round(degrees / 45) % 8];
}

function average(values) {
    const valid = values.filter(Number.isFinite);
    return valid.length
        ? valid.reduce((sum, value) => sum + value, 0) / valid.length
        : null;
}

function formatValue(value, suffix = "") {
    return Number.isFinite(value) ? `${Math.round(value)}${suffix}` : "N/A";
}

function formatDate(dateString, options = {}) {
    return new Date(dateString + "T12:00:00").toLocaleDateString("en-US", options);
}

function formatFishingHour(hour) {
    const normalized = ((hour % 24) + 24) % 24;
    return `${normalized % 12 || 12}:00 ${normalized >= 12 ? "PM" : "AM"}`;
}

function formatFishingWindow(window) {
    if (!window) return "Not available";
    return `${formatFishingHour(window.start)} – ${formatFishingHour(window.end)}`;
}

// Still used for the Temperature bar and the hourly windows (no backend scorer for those yet)
function calculateBiteScore(day) {
    const scores = {
        pressure: clamp(10 - Math.abs(day.pressure - 1013) / 5),
        temperature: clamp(10 - Math.abs(day.temperature - 68) / 5.4),
        clouds: clamp(10 - Math.abs(day.clouds - 60) / 12),
        rain: clamp(10 - day.rain * 2),
        surf: clamp(10 - (day.wind * 1.609344) / 5)
    };

    const overall =
        scores.pressure * 0.25 +
        scores.temperature * 0.25 +
        scores.clouds * 0.20 +
        scores.rain * 0.15 +
        scores.surf * 0.15;

    return {
        score: Math.max(1, Math.round(overall)),
        rawScore: overall,
        factors: scores
    };
}

// Open-Meteo is now only used for the weather panel and hourly data, using the spot's coordinates
async function getWeather(latitude, longitude) {
    const params = new URLSearchParams({
        latitude,
        longitude,
        current: "temperature_2m,wind_speed_10m,wind_direction_10m,pressure_msl",
        daily: "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,sunrise,sunset",
        hourly: "pressure_msl,cloud_cover,precipitation_probability,temperature_2m,wind_speed_10m,precipitation",
        temperature_unit: "fahrenheit",
        wind_speed_unit: "mph",
        timezone: "auto",
        forecast_days: 7
    });

    const response = await fetch(`https://api.open-meteo.com/v1/forecast?${params}`);

    if (!response.ok) throw new Error("Unable to retrieve weather data.");

    const data = await response.json();

    if (!data.daily || !data.hourly || !data.current) {
        throw new Error("Weather data unavailable.");
    }

    return data;
}

// Day scores and factor bars come from the backend; weather fields come from Open-Meteo
function processForecast(weather, scoreData) {
    return scoreData.days.map(backendDay => {
        const i = weather.daily.time.indexOf(backendDay.date);
        if (i === -1) return null;

        const indices = weather.hourly.time
            .map((time, j) => time.startsWith(backendDay.date) ? j : -1)
            .filter(j => j !== -1);

        const day = {
            date: backendDay.date,
            temperature: (weather.daily.temperature_2m_max[i] + weather.daily.temperature_2m_min[i]) / 2,
            rain: weather.daily.precipitation_sum[i] ?? 0,
            rainChance: weather.daily.precipitation_probability_max[i] ?? null,
            wind: weather.daily.wind_speed_10m_max[i] ?? 0,
            pressure: average(indices.map(j => weather.hourly.pressure_msl[j])) ?? 1013,
            clouds: average(indices.map(j => weather.hourly.cloud_cover[j])) ?? 0,
            sunrise: weather.daily.sunrise[i],
            sunset: weather.daily.sunset[i]
        };

        // bar values on the 0-10 scale; null means the backend had no data
        const bars = {};
        for (const [barId, key] of Object.entries(factorMap)) {
            const value = backendDay.factors[key];
            bars[barId] = Number.isFinite(value) ? value / 10 : null;
        }
        const score = backendDay.score / 10;   // keeps one decimal
        return {...day, score, rawScore: score, factors: bars, explanation: backendDay.explanation};
    }).filter(Boolean);
}

function calculateHourlyFishingScore(hour, day) {
    const result = calculateBiteScore(hour);
    const hourTime = hour.hour + 0.5;

    const sunrise = day.sunrise
        ? Number(day.sunrise.substring(11, 13)) + Number(day.sunrise.substring(14, 16)) / 60
        : 6;

    const sunset = day.sunset
        ? Number(day.sunset.substring(11, 13)) + Number(day.sunset.substring(14, 16)) / 60
        : 18;

    let bonus = 0;

    if (Math.abs(hourTime - sunrise) <= 2) bonus = 0.7;
    else if (Math.abs(hourTime - sunset) <= 2) bonus = 0.6;

    return clamp(result.rawScore + bonus);
}

function processHourlyForecast(data, days) {
    return data.hourly.time.map((time, index) => {
        const date = time.substring(0, 10);
        const day = days.find(item => item.date === date);

        const hour = {
            time,
            date,
            hour: Number(time.substring(11, 13)),
            temperature: data.hourly.temperature_2m[index],
            rain: data.hourly.precipitation[index] ?? 0,
            clouds: data.hourly.cloud_cover[index] ?? 0,
            pressure: data.hourly.pressure_msl[index] ?? 1013,
            wind: data.hourly.wind_speed_10m[index] ?? 0
        };

        return {...hour, score: day ? calculateHourlyFishingScore(hour, day) : 0};
    });
}

function getCurrentRainChance(data) {
    const current = Date.parse(`${data.current.time}Z`);
    let nearest = 0;
    let difference = Infinity;

    data.hourly.time.forEach((time, index) => {
        const distance = Math.abs(Date.parse(`${time}Z`) - current);

        if (distance < difference) {
            difference = distance;
            nearest = index;
        }
    });

    return data.hourly.precipitation_probability[nearest] ?? null;
}

function getFishingWindows(date) {
    const hours = hourlyFishingForecast.filter(hour => hour.date === date);
    const windows = [];

    for (let i = 0; i <= hours.length - 3; i++) {
        const group = hours.slice(i, i + 3);

        if (group[1].hour !== group[0].hour + 1 || group[2].hour !== group[1].hour + 1) {
            continue;
        }

        windows.push({
            start: group[0].hour,
            end: group[2].hour + 1,
            score: average(group.map(hour => hour.score))
        });
    }

    return windows.sort((a, b) => b.score - a.score);
}

function getTopFishingWindows(date, limit = 3) {
    const selected = [];

    for (const window of getFishingWindows(date)) {
        const overlaps = selected.some(item => window.start < item.end && window.end > item.start);

        if (!overlaps) selected.push(window);
        if (selected.length === limit) break;
    }

    return selected;
}

function getRecommendationReason(day) {
    const reasons = [];

    if (day.factors.pressure >= 7) reasons.push("favorable atmospheric pressure");
    if (day.factors.temperature >= 7) reasons.push("comfortable temperatures");
    if (day.factors.clouds >= 7) reasons.push("good cloud coverage");
    if (day.factors.rain >= 7) reasons.push("low precipitation");
    if (day.factors.surf >= 7) reasons.push("manageable wind conditions");

    return reasons.length
        ? `🎃 The fishing spirits favor this day because of ${reasons.join(", ")}.`
        : "🔮 This day has the strongest combined fishing conditions of the week.";
}

function displayForecast() {
    dateBlocks.innerHTML = "";

    forecastDays.forEach((day, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `day ${index === selectedDay ? "selected" : ""}`;
        button.setAttribute("aria-pressed", String(index === selectedDay));

        button.innerHTML = `
            <span class="date">${formatDate(day.date, {month: "short", day: "numeric"})}</span>
            <span class="score" style="color:${getScoreColor(day.score)}">${formatScore(day.score)}</span>
            <span class="day-pumpkin">${day.score >= 8 ? "🎃" : day.score >= 5 ? "🦇" : "👻"}</span>
        `;

        button.addEventListener("click", () => selectForecastDay(index));
        dateBlocks.appendChild(button);
    });
}

function updateMainRating(index) {
    const day = forecastDays[index];
    if (!day) return;

    overallRating.textContent = `${formatScore(day.score)}/10`;
    overallRating.style.color = getScoreColor(day.score);
    ratingMessage.textContent = getRatingMessage(day.score);
    scoreExplanation.textContent = day.explanation?.summary ?? "A detailed explanation is unavailable for this forecast.";

    factors.forEach(factor => {
        const bar = document.getElementById(factor);
        if (!bar) return;

        const score = day.factors[factor];
        const detail = document.getElementById(`${factor}-explanation`);
        if (detail) {
            detail.textContent = day.explanation?.factors?.[factorMap[factor]] ?? "Factor details unavailable.";
        }

        // null means the backend had no data for this factor
        if (score === null || score === undefined) {
            bar.style.width = "0%";
            bar.style.backgroundColor = "transparent";
            return;
        }

        bar.style.width = `${score * 10}%`;
        bar.style.backgroundColor = getScoreColor(score);
    });
}

function updateWeatherConditions(index) {
    const day = forecastDays[index];
    if (!day) return;

    if (index === 0 && currentWeather) {
        weatherTemperature.textContent = formatValue(currentWeather.temperature_2m, "°F");
        weatherRain.textContent = formatValue(currentWeather.rainChance, "%");
        weatherWind.textContent = formatValue(currentWeather.wind_speed_10m, " mph");
        weatherPressure.textContent = formatValue(currentWeather.pressure_msl, " hPa");
        windDirection.textContent = `Direction: ${getWindDirection(currentWeather.wind_direction_10m)}`;
        weatherTitle.textContent = `🌙 Current Weather — ${currentCity}`;
        weatherBadge.textContent = "Current";
        weatherBadge.classList.remove("forecast-badge");
    } else {
        weatherTemperature.textContent = formatValue(day.temperature, "°F");
        weatherRain.textContent = formatValue(day.rainChance, "%");
        weatherWind.textContent = formatValue(day.wind, " mph");
        weatherPressure.textContent = formatValue(day.pressure, " hPa");
        windDirection.textContent = "Maximum forecast wind";
        weatherTitle.textContent = `🔮 Forecast — ${formatDate(day.date, {month: "short", day: "numeric"})}`;
        weatherBadge.textContent = "Forecast";
        weatherBadge.classList.add("forecast-badge");
    }

    if (currentWeather?.time) {
        weatherUpdated.textContent = `Weather model time: ${currentWeather.time.replace("T", " ")}`;
    }
}

function displayFishingRecommendations() {
    if (!forecastDays.length) return;

    const ranked = forecastDays.map((day, index) => ({
        ...day,
        originalIndex: index,
        bestWindow: getTopFishingWindows(day.date, 1)[0] ?? null
    }));

    ranked.sort((a, b) =>
        b.rawScore - a.rawScore ||
        (b.bestWindow?.score ?? 0) - (a.bestWindow?.score ?? 0)
    );

    const best = ranked[0];

    bestDayName.textContent = formatDate(best.date, {weekday: "long", month: "short", day: "numeric"});
    bestDayScore.textContent = `${formatScore(best.score)}/10`;
    bestDayScore.style.color = getScoreColor(best.score);
    bestDayReason.textContent = getRecommendationReason(best);
    bestDayTime.textContent = formatFishingWindow(best.bestWindow);

    fishingTimesList.innerHTML = "";

    ranked.forEach((day, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `fishing-time-row ${day.originalIndex === selectedDay ? "active" : ""}`;

        button.innerHTML = `
            <div class="fishing-rank">${index === 0 ? "🏆" : `#${index + 1}`}</div>
            <div class="fishing-time-info">
                <h3>${formatDate(day.date, {weekday: "long", month: "short", day: "numeric"})}</h3>
                <p>🎣 Best time: ${formatFishingWindow(day.bestWindow)}</p>
            </div>
            <div class="fishing-time-score" style="color:${getScoreColor(day.score)}">${formatScore(day.score)}/10</div>
        `;

        button.addEventListener("click", () => {
            selectForecastDay(day.originalIndex);
            switchTab("fishing-times");
        });

        fishingTimesList.appendChild(button);
    });
}

function updateHourlyDaySelector() {
    hourlyDaySelect.innerHTML = "";

    forecastDays.forEach((day, index) => {
        const option = document.createElement("option");
        option.value = index;
        option.textContent = formatDate(day.date, {weekday: "long", month: "short", day: "numeric"});
        hourlyDaySelect.appendChild(option);
    });

    hourlyDaySelect.value = String(selectedDay);
}

hourlyDaySelect.addEventListener("change", () => {
    const index = Number(hourlyDaySelect.value);
    if (forecastDays[index]) selectForecastDay(index);
});

function displayHourlyRecommendations(index) {
    const day = forecastDays[index];
    if (!day) return;

    hourlyTitle.textContent = `🌙 Top Fishing Times — ${formatDate(day.date, {weekday: "long", month: "short", day: "numeric"})}`;

    const windows = getTopFishingWindows(day.date, 3);
    hourlyTimesList.innerHTML = "";

    if (!windows.length) {
        hourlyTimesList.innerHTML = '<p class="empty-message">👻 No hourly recommendations available.</p>';
        return;
    }

    windows.forEach((window, rank) => {
        const card = document.createElement("div");
        card.className = "hourly-window-card";

        card.innerHTML = `
            <div class="hourly-window-info">
                <h3>${rank === 0 ? "🎃" : rank === 1 ? "🦇" : "👻"} #${rank + 1} — ${formatFishingWindow(window)}</h3>
                <p>Weather-based fishing score</p>
            </div>
            <div class="hourly-window-score" style="color:${getScoreColor(window.score)}">${window.score.toFixed(1)}/10</div>
        `;

        hourlyTimesList.appendChild(card);
    });
}

function selectForecastDay(index) {
    selectedDay = index;
    displayForecast();
    updateMainRating(index);
    updateWeatherConditions(index);
    displayFishingRecommendations();
    displayHourlyRecommendations(index);
    hourlyDaySelect.value = String(index);
}

function applyWeatherData(weather, scoreData, preserveSelection = false) {
    currentWeather = {...weather.current, rainChance: getCurrentRainChance(weather)};
    forecastDays = processForecast(weather, scoreData);

    if (!forecastDays.length) {
        throw new Error("No forecast is available for this spot right now.");
    }

    hourlyFishingForecast = processHourlyForecast(weather, forecastDays);

    if (!preserveSelection) selectedDay = 0;
    selectedDay = Math.max(0, Math.min(selectedDay, forecastDays.length - 1));

    updateHourlyDaySelector();
    selectForecastDay(selectedDay);
}

async function searchSpot(query) {
    const requestId = ++requestCounter;
    ++weatherRequestCounter;

    try {
        searchButton.disabled = true;
        searchButton.textContent = "Summoning...";

        if (!spots.length) {
            spots = await getSpots();
            fillSpotList();
        }

        const spot = findSpot(query);
        if (!spot) throw new Error("No fishing spot matches that name.");

        const [scoreData, weather] = await Promise.all([
            getScoreData(spot.id),
            getWeather(spot.latitude, spot.longitude)
        ]);

        if (requestId !== requestCounter) return;

        currentSpot = spot;
        currentCity = spotName(spot);
        currentCoordinates = {latitude: spot.latitude, longitude: spot.longitude};

        applyWeatherData(weather, scoreData);
        searchInput.value = currentCity;
    } catch (error) {
        if (requestId === requestCounter) {
            alert(error.message);
            console.error(error);
        }
    } finally {
        if (requestId === requestCounter) {
            searchButton.disabled = false;
            searchButton.textContent = "Search 🎃";
        }
    }
}

async function refreshWeather() {
    if (!currentSpot || document.hidden || refreshInProgress) return;

    refreshInProgress = true;
    const refreshId = ++weatherRequestCounter;
    const searchId = requestCounter;

    try {
        const [scoreData, weather] = await Promise.all([
            getScoreData(currentSpot.id),
            getWeather(currentSpot.latitude, currentSpot.longitude)
        ]);

        if (refreshId !== weatherRequestCounter || searchId !== requestCounter) return;

        applyWeatherData(weather, scoreData, true);
    } catch (error) {
        console.error("Weather refresh failed:", error);
    } finally {
        refreshInProgress = false;
    }
}

searchForm.addEventListener("submit", event => {
    event.preventDefault();
    const query = searchInput.value.trim();

    if (!query) return alert("Please enter a fishing spot name.");

    searchSpot(query);
});

const COMMUNITY_STORAGE_KEY = "fisch-community-posts-v1";
const COMMUNITY_VOTES_KEY = "fisch-community-votes-v1";

function loadStoredJSON(key, fallback) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : fallback;
    } catch (error) {
        return fallback;
    }
}

function saveStoredJSON(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        alert("Unable to save data in this browser.");
        return false;
    }
}

let posts = loadStoredJSON(COMMUNITY_STORAGE_KEY, []);
let userVotes = loadStoredJSON(COMMUNITY_VOTES_KEY, {});

if (!Array.isArray(posts)) posts = [];
if (!userVotes || typeof userVotes !== "object" || Array.isArray(userVotes)) userVotes = {};

function generateId() {
    if (window.crypto?.randomUUID) return crypto.randomUUID();
    return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function timeAgo(timestamp) {
    const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));

    if (seconds < 60) return "just now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;

    return new Date(timestamp).toLocaleDateString("en-US");
}

function createElement(tag, className = "", text = "") {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== "") element.textContent = text;
    return element;
}

function getPostScore(post) {
    return (post.upvotes || 0) - (post.downvotes || 0);
}

function getFilteredPosts() {
    const query = communitySearch.value.trim().toLowerCase();
    const category = communityCategory.value;
    const sort = communitySort.value;

    const filtered = posts.filter(post => {
        const matchesCategory = category === "all" || post.category === category;
        const matchesSearch = `${post.title} ${post.content} ${post.author}`.toLowerCase().includes(query);
        return matchesCategory && matchesSearch;
    });

    filtered.sort((a, b) => {
        if (sort === "top") return getPostScore(b) - getPostScore(a) || b.createdAt - a.createdAt;
        if (sort === "discussed") return b.comments.length - a.comments.length || b.createdAt - a.createdAt;
        return b.createdAt - a.createdAt;
    });

    return filtered;
}

function updateCommunityStats() {
    const totalComments = posts.reduce((sum, post) => sum + post.comments.length, 0);

    document.getElementById("total-posts").textContent = posts.length;
    document.getElementById("total-comments").textContent = totalComments;
    document.getElementById("post-count").textContent = `${getFilteredPosts().length} posts`;
}

function voteOnPost(postId, direction) {
    const post = posts.find(item => item.id === postId);
    if (!post) return;

    const previous = userVotes[postId] || 0;

    if (previous === 1) post.upvotes = Math.max(0, post.upvotes - 1);
    if (previous === -1) post.downvotes = Math.max(0, post.downvotes - 1);

    const next = previous === direction ? 0 : direction;

    if (next === 1) post.upvotes++;
    if (next === -1) post.downvotes++;

    if (next === 0) delete userVotes[postId];
    else userVotes[postId] = next;

    saveStoredJSON(COMMUNITY_STORAGE_KEY, posts);
    saveStoredJSON(COMMUNITY_VOTES_KEY, userVotes);
    renderCommunity();
}

function renderComments(post, container) {
    container.innerHTML = "";

    if (!post.comments.length) {
        container.appendChild(createElement("p", "empty-message", "No replies yet. Be the first to help!"));
    }

    post.comments.forEach(comment => {
        const commentElement = createElement("div", "comment");
        const meta = createElement("div", "comment-meta");
        meta.appendChild(document.createTextNode(`🎣 u/${comment.author} `));
        meta.appendChild(createElement("span", "", `· ${timeAgo(comment.createdAt)}`));

        commentElement.appendChild(meta);
        commentElement.appendChild(createElement("p", "", comment.content));
        container.appendChild(commentElement);
    });

    const form = createElement("form", "comment-form");

    const author = createElement("input");
    author.placeholder = "Your username";
    author.maxLength = 40;
    author.required = true;

    const content = createElement("textarea");
    content.placeholder = "Write a helpful reply...";
    content.rows = 3;
    content.maxLength = 1500;
    content.required = true;

    const submit = createElement("button", "", "Reply 🎣");
    submit.type = "submit";

    form.append(author, content, submit);

    form.addEventListener("submit", event => {
        event.preventDefault();

        const name = author.value.trim();
        const message = content.value.trim();

        if (!name || !message) return;

        post.comments.push({
            id: generateId(),
            author: name,
            content: message,
            createdAt: Date.now()
        });

        if (saveStoredJSON(COMMUNITY_STORAGE_KEY, posts)) {
            renderCommunity(post.id);
        }
    });

    container.appendChild(form);
}

function renderCommunity(openPostId = null) {
    const filtered = getFilteredPosts();
    communityPosts.innerHTML = "";

    if (!filtered.length) {
        communityPosts.appendChild(createElement("p", "empty-message", "👻 No discussions found. Start the first one!"));
    }

    filtered.forEach(post => {
        const article = createElement("article", "community-post");
        const votes = createElement("div", "post-votes");

        const up = createElement("button", `vote-button ${userVotes[post.id] === 1 ? "voted" : ""}`, "▲");
        up.type = "button";
        up.setAttribute("aria-label", "Upvote post");
        up.addEventListener("click", () => voteOnPost(post.id, 1));

        const score = createElement("span", "vote-score", String(getPostScore(post)));

        const down = createElement("button", `vote-button ${userVotes[post.id] === -1 ? "voted" : ""}`, "▼");
        down.type = "button";
        down.setAttribute("aria-label", "Downvote post");
        down.addEventListener("click", () => voteOnPost(post.id, -1));

        votes.append(up, score, down);

        const body = createElement("div", "post-body");
        const meta = createElement("div", "post-meta");
        meta.appendChild(createElement("span", "post-category", post.category));
        meta.appendChild(createElement("span", "", `u/${post.author}`));
        meta.appendChild(createElement("span", "", `· ${timeAgo(post.createdAt)}`));

        const title = createElement("h3", "post-title", post.title);
        const content = createElement("p", "post-content", post.content);

        const actions = createElement("div", "post-actions");
        const replyButton = createElement("button", "post-action", `💬 ${post.comments.length} Replies`);
        replyButton.type = "button";

        const commentsContainer = createElement("div", "comments-container");
        commentsContainer.hidden = openPostId !== post.id;

        replyButton.addEventListener("click", () => {
            commentsContainer.hidden = !commentsContainer.hidden;

            if (!commentsContainer.hidden) {
                renderComments(post, commentsContainer);
            }
        });

        actions.appendChild(replyButton);
        body.append(meta, title, content, actions, commentsContainer);
        article.append(votes, body);
        communityPosts.appendChild(article);

        if (!commentsContainer.hidden) {
            renderComments(post, commentsContainer);
        }
    });

    updateCommunityStats();
}

postForm.addEventListener("submit", event => {
    event.preventDefault();

    const author = document.getElementById("post-author").value.trim();
    const title = document.getElementById("post-title").value.trim();
    const category = document.getElementById("post-category").value;
    const content = document.getElementById("post-content").value.trim();

    if (!author || !title || !content) return;

    const post = {
        id: generateId(),
        author,
        title,
        category,
        content,
        createdAt: Date.now(),
        upvotes: 0,
        downvotes: 0,
        comments: []
    };

    posts.unshift(post);

    if (saveStoredJSON(COMMUNITY_STORAGE_KEY, posts)) {
        postForm.reset();
        communitySearch.value = "";
        communityCategory.value = "all";
        communitySort.value = "newest";
        renderCommunity();
    }
});

communitySearch.addEventListener("input", () => renderCommunity());
communityCategory.addEventListener("change", () => renderCommunity());
communitySort.addEventListener("change", () => renderCommunity());

renderCommunity();

setInterval(() => {
    refreshWeather();
}, 10 * 60 * 1000);

async function init() {
    try {
        spots = await getSpots();
        fillSpotList();

        if (spots.length > 0) {
            await searchSpot(spotName(spots[0]));
        }
    } catch (error) {
        console.error(error);
        ratingMessage.textContent = error instanceof TypeError
            ? "Can't reach the forecast server. Start the backend and refresh."
            : error.message;
    }
}

init();
