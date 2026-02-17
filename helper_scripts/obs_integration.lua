obs = obslua

local bat_path = ""
local auto_start = false
local has_started = false

------------------------------------------------------------
-- Start batch file
------------------------------------------------------------
local function start_bat()
    if has_started then
        return
    end

    if bat_path == nil or bat_path == "" then
        obs.script_log(obs.LOG_WARNING, "No start.bat path specified.")
        return
    end

    -- Run batch directly (no extra window)
    local command = '"' .. bat_path .. '"'
    os.execute(command)

    has_started = true
    obs.script_log(obs.LOG_INFO, "Autostarted: " .. bat_path)
end

------------------------------------------------------------
-- Delayed autostart (called via timer)
------------------------------------------------------------
local function delayed_start()
    obs.timer_remove(delayed_start)

    if auto_start then
        start_bat()
    end
end

------------------------------------------------------------
-- OBS UI
------------------------------------------------------------
function script_properties()
    local props = obs.obs_properties_create()

    obs.obs_properties_add_path(
        props,
        "bat_path",
        "Path to start.bat",
        obs.OBS_PATH_FILE,
        "Batch Files (*.bat);;All Files (*.*)",
        nil
    )

    obs.obs_properties_add_bool(
        props,
        "auto_start",
        "Autostart when OBS starts"
    )

    return props
end

------------------------------------------------------------
-- Save settings
------------------------------------------------------------
function script_update(settings)
    bat_path = obs.obs_data_get_string(settings, "bat_path")
    auto_start = obs.obs_data_get_bool(settings, "auto_start")
end

------------------------------------------------------------
-- Called when script loads
------------------------------------------------------------
function script_load(settings)
    -- Wait 1 second after OBS loads
    obs.timer_add(delayed_start, 1000)
end

------------------------------------------------------------
-- Description
------------------------------------------------------------
function script_description()
    return "Automatically starts your start.bat when OBS launches."
end
