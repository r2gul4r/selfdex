#!/usr/bin/env node

"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const INSTALLER_PATH = path.join(PACKAGE_ROOT, "install.ps1");
const PACKAGE_JSON = require(path.join(PACKAGE_ROOT, "package.json"));

function printMainHelp() {
  console.log(`Selfdex ${PACKAGE_JSON.version}

Usage:
  selfdex install [options]
  selfdex doctor [options]
  selfdex --help
  selfdex --version

Commands:
  install    Clone or update Selfdex, then install the @selfdex Codex plugin.
  doctor     Check whether the local Selfdex setup is ready.

Install options:
  --dry-run                 Show what would happen without cloning or installing.
  --install-root <path>     Selfdex checkout path. Defaults to $HOME/selfdex.
  --plugin-home <path>      Codex plugin home. Defaults to CODEX_HOME or $HOME/.codex.
  --repo-url <url>          Git repository URL used by the bootstrap installer.
  --branch <name>           Git branch used by the bootstrap installer.
  --skip-plugin-install     Clone or update Selfdex without installing @selfdex.
  --skip-doctor             Do not run the setup doctor after install.
  --python <path>           Python executable used by the plugin installer.
  -h, --help                Show install help.
`);
}

function printInstallHelp() {
  console.log(`Usage:
  selfdex install [options]

Options:
  --dry-run                 Show what would happen without cloning or installing.
  --install-root <path>     Selfdex checkout path. Defaults to $HOME/selfdex.
  --plugin-home <path>      Codex plugin home. Defaults to CODEX_HOME or $HOME/.codex.
  --repo-url <url>          Git repository URL used by the bootstrap installer.
  --branch <name>           Git branch used by the bootstrap installer.
  --skip-plugin-install     Clone or update Selfdex without installing @selfdex.
  --skip-doctor             Do not run the setup doctor after install.
  --python <path>           Python executable used by the plugin installer.
  -h, --help                Show this help.
`);
}

function printDoctorHelp() {
  console.log(`Usage:
  selfdex doctor [options]

Options:
  --install-root <path>     Selfdex checkout path. Defaults to $HOME/selfdex.
  --home <path>             Codex plugin home. Defaults to CODEX_HOME or $HOME/.codex.
  --codex-home <path>       Codex home directory. Defaults to CODEX_HOME or $HOME/.codex.
  --format <json|markdown>  Output format. Defaults to markdown.
  --python <path>           Run the legacy Python setup doctor with this executable.
  -h, --help                Show this help.
`);
}

function fail(message, code = 1) {
  console.error(`selfdex: ${message}`);
  process.exit(code);
}

function takeValue(args, index, flag) {
  const value = args[index + 1];
  if (!value || value.startsWith("-")) {
    fail(`${flag} requires a value`);
  }
  return value;
}

function parseInstallArgs(args) {
  const options = {
    dryRun: false,
    installRoot: null,
    pluginHome: null,
    repoUrl: null,
    branch: null,
    skipPluginInstall: false,
    skipDoctor: false,
    python: null,
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    switch (arg) {
      case "-h":
      case "--help":
        options.help = true;
        break;
      case "--dry-run":
        options.dryRun = true;
        break;
      case "--install-root":
        options.installRoot = takeValue(args, index, arg);
        index += 1;
        break;
      case "--plugin-home":
        options.pluginHome = takeValue(args, index, arg);
        index += 1;
        break;
      case "--repo-url":
        options.repoUrl = takeValue(args, index, arg);
        index += 1;
        break;
      case "--branch":
        options.branch = takeValue(args, index, arg);
        index += 1;
        break;
      case "--skip-plugin-install":
        options.skipPluginInstall = true;
        break;
      case "--skip-doctor":
        options.skipDoctor = true;
        break;
      case "--python":
        options.python = takeValue(args, index, arg);
        index += 1;
        break;
      default:
        fail(`unknown install option: ${arg}`);
    }
  }

  return options;
}

function parseDoctorArgs(args) {
  const options = {
    installRoot: null,
    home: null,
    codexHome: null,
    format: "markdown",
    python: null,
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    switch (arg) {
      case "-h":
      case "--help":
        options.help = true;
        break;
      case "--install-root":
        options.installRoot = takeValue(args, index, arg);
        index += 1;
        break;
      case "--home":
        options.home = takeValue(args, index, arg);
        index += 1;
        break;
      case "--codex-home":
        options.codexHome = takeValue(args, index, arg);
        index += 1;
        break;
      case "--format":
        options.format = takeValue(args, index, arg);
        index += 1;
        if (!["json", "markdown"].includes(options.format)) {
          fail("--format must be json or markdown");
        }
        break;
      case "--python":
        options.python = takeValue(args, index, arg);
        index += 1;
        break;
      default:
        fail(`unknown doctor option: ${arg}`);
    }
  }

  return options;
}

function commandExists(command) {
  const checker =
    process.platform === "win32"
      ? ["where.exe", [command]]
      : ["sh", ["-c", `command -v ${command} >/dev/null 2>&1`]];
  const result = spawnSync(checker[0], checker[1], { stdio: "ignore" });
  return !result.error && result.status === 0;
}

function resolvePowerShell() {
  const candidates =
    process.platform === "win32"
      ? ["powershell.exe", "pwsh.exe", "pwsh"]
      : ["pwsh", "powershell"];

  for (const candidate of candidates) {
    if (commandExists(candidate)) {
      return candidate;
    }
  }
  return null;
}

function resolvePython(explicit) {
  if (explicit) {
    return [explicit];
  }

  const bundled = path.join(
    os.homedir(),
    ".cache",
    "codex-runtimes",
    "codex-primary-runtime",
    "dependencies",
    "python",
    process.platform === "win32" ? "python.exe" : "python"
  );
  if (fs.existsSync(bundled)) {
    return [bundled];
  }

  const candidates = process.platform === "win32" ? ["python.exe", "python", "py.exe", "py"] : ["python3", "python"];
  for (const candidate of candidates) {
    if (commandExists(candidate)) {
      return candidate.startsWith("py") ? [candidate, "-3"] : [candidate];
    }
  }
  return null;
}

function defaultInstallRoot() {
  return path.join(os.homedir(), "selfdex");
}

function defaultCodexHome() {
  return path.resolve(process.env.CODEX_HOME || path.join(os.homedir(), ".codex"));
}

function normalizePathForCompare(value) {
  const resolved = path.resolve(value);
  return process.platform === "win32" ? resolved.toLowerCase() : resolved;
}

function readJsonFile(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function checkResult(checkId, category, status, severity, summary, checkPath = "") {
  return {
    check_id: checkId,
    category,
    status,
    severity,
    summary,
    path: checkPath,
  };
}

function pathExists(filePath) {
  try {
    return fs.existsSync(filePath);
  } catch (_error) {
    return false;
  }
}

function marketplaceHasSelfdex(marketplacePath) {
  if (!pathExists(marketplacePath)) {
    return false;
  }
  try {
    const payload = readJsonFile(marketplacePath);
    return Array.isArray(payload.plugins) && payload.plugins.some((entry) => entry && entry.name === "selfdex");
  } catch (_error) {
    return false;
  }
}

function pluginCacheResult(codexHome, relPath, checkId, label) {
  const pluginPath = path.join(codexHome, ...relPath);
  if (pathExists(pluginPath)) {
    return checkResult(checkId, "recommended_integration", "pass", "info", `${label} plugin appears available.`, pluginPath);
  }
  return checkResult(
    checkId,
    "recommended_integration",
    "manual_action",
    "medium",
    `${label} plugin was not found in the local Codex plugin cache; install/connect it in Codex if that workflow is needed.`,
    pluginPath
  );
}

function fileTextIncludes(filePath, snippets) {
  if (!pathExists(filePath)) {
    return { exists: false, missing: snippets };
  }
  try {
    const text = fs.readFileSync(filePath, "utf8");
    return {
      exists: true,
      missing: snippets.filter((snippet) => !text.includes(snippet)),
    };
  } catch (error) {
    return { exists: true, error: error.message, missing: snippets };
  }
}

function codexPolicyResult(root, checkId, relPath, requiredSnippets) {
  const policyPath = path.join(root, ...relPath);
  const check = fileTextIncludes(policyPath, requiredSnippets);
  const displayPath = relPath.join("/");
  if (!check.exists) {
    return checkResult(
      checkId,
      "subagent_policy",
      "fail",
      "high",
      `Project-scoped Codex subagent policy file is missing: ${displayPath}`,
      policyPath
    );
  }
  if (check.error) {
    return checkResult(
      checkId,
      "subagent_policy",
      "fail",
      "high",
      `Project-scoped Codex subagent policy file could not be read: ${check.error}`,
      policyPath
    );
  }
  if (check.missing.length > 0) {
    return checkResult(
      checkId,
      "subagent_policy",
      "fail",
      "high",
      `Project-scoped Codex subagent policy file is stale; missing: ${check.missing.join(", ")}`,
      policyPath
    );
  }
  return checkResult(
    checkId,
    "subagent_policy",
    "pass",
    "info",
    `Project-scoped Codex subagent policy file is present: ${displayPath}`,
    policyPath
  );
}

function sourceFileResult(root, relPath) {
  const sourcePath = path.join(root, ...relPath);
  const displayPath = relPath.join("/");
  const exists = pathExists(sourcePath);
  return checkResult(
    `selfdex-source-${relPath[relPath.length - 1]}`,
    "core",
    exists ? "pass" : "fail",
    exists ? "info" : "high",
    `Required Selfdex source file ${exists ? "exists" : "is missing"}: ${displayPath}`,
    sourcePath
  );
}

function rootConfigStatus(root, rootConfigPath) {
  if (!pathExists(rootConfigPath)) {
    return "missing";
  }
  try {
    const payload = readJsonFile(rootConfigPath);
    return normalizePathForCompare(String(payload.selfdex_root || "")) === normalizePathForCompare(root) ? "match" : "mismatch";
  } catch (_error) {
    return "invalid";
  }
}

function buildNodeDoctorPayload(options) {
  const installRoot = path.resolve(options.installRoot || defaultInstallRoot());
  const codexHome = path.resolve(options.codexHome || defaultCodexHome());
  const home = path.resolve(options.home || codexHome);
  const targetPlugin = path.join(home, "plugins", "selfdex");
  const targetSkill = path.join(home, "skills", "selfdex", "SKILL.md");
  const marketplacePath = path.join(home, ".agents", "plugins", "marketplace.json");
  const rootConfigPath = path.join(targetPlugin, "selfdex-root.json");

  const codexPolicyFiles = [
    [
      "codex-config",
      [".codex", "config.toml"],
      ["multi_agent = true", "[agents.explorer]", "[agents.worker]", "[agents.reviewer]", "[agents.docs_researcher]"],
    ],
    [
      "codex-agent-explorer",
      [".codex", "agents", "explorer.toml"],
      ['name = "explorer"', 'model = "gpt-5.5"', 'model_reasoning_effort = "low"', 'sandbox_mode = "read-only"'],
    ],
    [
      "codex-agent-worker",
      [".codex", "agents", "worker.toml"],
      ['name = "worker"', 'model = "gpt-5.5"', 'model_reasoning_effort = "high"', "frozen task slice", "declared write boundary"],
    ],
    [
      "codex-agent-reviewer",
      [".codex", "agents", "reviewer.toml"],
      ['name = "reviewer"', 'model = "gpt-5.5"', 'model_reasoning_effort = "xhigh"', 'sandbox_mode = "read-only"'],
    ],
    [
      "codex-agent-docs-researcher",
      [".codex", "agents", "docs-researcher.toml"],
      ['name = "docs_researcher"', 'model = "gpt-5.5"', 'model_reasoning_effort = "medium"', 'sandbox_mode = "read-only"'],
    ],
  ];

  const checks = [
    checkResult("node-doctor", "runtime", "pass", "info", "Node-native setup doctor is running; Python is not required for this check.", process.execPath),
    checkResult(
      "git-command",
      "runtime",
      commandExists("git") ? "pass" : "fail",
      commandExists("git") ? "info" : "high",
      commandExists("git") ? "Git is available for checkout updates." : "Missing required command. Tried: git."
    ),
    sourceFileResult(installRoot, ["scripts", "plan_external_project.py"]),
    sourceFileResult(installRoot, ["scripts", "run_target_codex.py"]),
    sourceFileResult(installRoot, ["scripts", "check_github_actions_status.py"]),
    ...codexPolicyFiles.map(([checkId, relPath, snippets]) => codexPolicyResult(installRoot, checkId, relPath, snippets)),
  ];

  const pluginExists = pathExists(targetPlugin);
  checks.push(
    checkResult(
      "selfdex-plugin-directory",
      "core",
      pluginExists ? "pass" : "fail",
      pluginExists ? "info" : "high",
      pluginExists ? "Codex plugin home @selfdex directory is installed." : "Codex plugin home @selfdex directory is missing.",
      targetPlugin
    )
  );

  const marketplaceOk = marketplaceHasSelfdex(marketplacePath);
  checks.push(
    checkResult(
      "selfdex-marketplace-entry",
      "core",
      marketplaceOk ? "pass" : "fail",
      marketplaceOk ? "info" : "high",
      marketplaceOk ? "Codex plugin home marketplace includes the selfdex plugin entry." : "Codex plugin home marketplace is missing the selfdex plugin entry.",
      marketplacePath
    )
  );

  const skillExists = pathExists(targetSkill);
  checks.push(
    checkResult(
      "selfdex-global-skill",
      "core",
      skillExists ? "pass" : "fail",
      skillExists ? "info" : "high",
      skillExists ? "Codex global skill @selfdex entry is installed." : "Codex global skill @selfdex entry is missing; @ mention may fall back to file search.",
      targetSkill
    )
  );

  const configStatus = rootConfigStatus(installRoot, rootConfigPath);
  checks.push(
    checkResult(
      "selfdex-root-config",
      "core",
      configStatus === "match" ? "pass" : "fail",
      configStatus === "match" ? "info" : "high",
      `Installed plugin root config status: ${configStatus}.`,
      rootConfigPath
    )
  );

  const githubActionsPath = path.join(installRoot, "scripts", "check_github_actions_status.py");
  const githubActionsExists = pathExists(githubActionsPath);
  checks.push(
    checkResult(
      "github-actions-fallback",
      "fallback",
      githubActionsExists ? "pass" : "fail",
      githubActionsExists ? "info" : "medium",
      githubActionsExists ? "GitHub Actions API fallback checker is available." : "GitHub Actions API fallback checker is missing.",
      githubActionsPath
    )
  );
  checks.push(pluginCacheResult(codexHome, ["plugins", "cache", "openai-curated", "github"], "github-plugin", "GitHub"));
  checks.push(pluginCacheResult(codexHome, ["plugins", "cache", "openai-curated", "chatgpt-apps"], "chatgpt-apps-plugin", "ChatGPT Apps"));
  checks.push(
    checkResult(
      "gpt-pro-direction-review",
      "account_capability",
      "manual_action",
      "medium",
      "GPT Pro / GPT-5.5 direction review is an account/model entitlement and remains user-approved only."
    )
  );
  checks.push(checkResult("gmail-not-required", "integration_boundary", "pass", "info", "Gmail is not required for setup or GitHub CI feedback."));

  const highFailures = checks.filter((check) => check.status === "fail" && check.severity === "high");
  const manualActions = checks.filter((check) => check.status === "manual_action");
  let readiness = highFailures.length > 0 ? "blocked" : "ready";
  if (readiness === "ready" && manualActions.length > 0) {
    readiness = "ready_with_recommended_actions";
  }

  return {
    schema_version: 1,
    analysis_kind: "selfdex_setup_check",
    runtime: "node-native",
    status: highFailures.length === 0 ? "pass" : "fail",
    readiness,
    root: installRoot,
    home,
    codex_home: codexHome,
    check_count: checks.length,
    manual_action_count: manualActions.length,
    high_failure_count: highFailures.length,
    checks,
    next_step: nextDoctorStep(readiness, manualActions),
  };
}

function nextDoctorStep(readiness, manualActions) {
  if (readiness === "blocked") {
    return "Fix the failed core checks, then rerun selfdex doctor.";
  }
  if (manualActions.length > 0) {
    return "Core setup is usable. Connect recommended integrations in Codex when those workflows are needed.";
  }
  return "Core setup and recommended integrations look ready. Invoke @selfdex from a target project session.";
}

function renderDoctorMarkdown(payload) {
  const lines = [
    "# Selfdex Doctor",
    "",
    `- status: \`${payload.status}\``,
    `- readiness: \`${payload.readiness}\``,
    `- runtime: \`${payload.runtime}\``,
    `- root: \`${payload.root}\``,
    `- codex_home: \`${payload.codex_home}\``,
    "",
  ];
  const categories = [
    ["core", "Core"],
    ["subagent_policy", "Subagent Policy"],
    ["runtime", "Runtime"],
    ["recommended_integration", "Recommended Integrations"],
    ["fallback", "Fallbacks"],
    ["account_capability", "Account Capabilities"],
    ["integration_boundary", "Integration Boundary"],
  ];
  for (const [category, title] of categories) {
    const categoryChecks = payload.checks.filter((check) => check.category === category);
    if (categoryChecks.length === 0) {
      continue;
    }
    lines.push(`## ${title}`, "");
    for (const check of categoryChecks) {
      lines.push(`- \`${check.status}\` ${check.check_id}: ${check.summary}`);
    }
    lines.push("");
  }
  lines.push("## Next Step", "", payload.next_step);
  return `${lines.join("\n")}\n`;
}

function writeDoctorPayload(payload, format) {
  if (format === "json") {
    console.log(JSON.stringify(payload, null, 2));
  } else {
    process.stdout.write(renderDoctorMarkdown(payload));
  }
}

function buildPowerShellArgs(options) {
  const args = ["-NoProfile"];
  if (process.platform === "win32") {
    args.push("-ExecutionPolicy", "Bypass");
  }
  args.push("-File", INSTALLER_PATH);

  if (options.repoUrl) {
    args.push("-RepoUrl", options.repoUrl);
  }
  if (options.branch) {
    args.push("-Branch", options.branch);
  }
  if (options.installRoot) {
    args.push("-InstallRoot", options.installRoot);
  }
  if (options.pluginHome) {
    args.push("-PluginHome", options.pluginHome);
  }
  if (options.python) {
    args.push("-Python", options.python);
  }
  if (options.dryRun) {
    args.push("-DryRun");
  }
  if (options.skipPluginInstall) {
    args.push("-SkipPluginInstall");
  }
  if (options.skipDoctor) {
    args.push("-SkipDoctor");
  }

  return args;
}

function runInstall(args) {
  const options = parseInstallArgs(args);
  if (options.help) {
    printInstallHelp();
    return 0;
  }

  if (!fs.existsSync(INSTALLER_PATH)) {
    fail(`bootstrap installer not found: ${INSTALLER_PATH}`);
  }

  const powershell = resolvePowerShell();
  if (!powershell) {
    fail("PowerShell was not found. Install PowerShell, then rerun `npx selfdex install`.");
  }

  const result = spawnSync(powershell, buildPowerShellArgs(options), {
    stdio: "inherit",
  });

  if (result.error) {
    fail(result.error.message);
  }

  return result.status === null ? 1 : result.status;
}

function runPythonDoctor(options) {
  const installRoot = path.resolve(options.installRoot || defaultInstallRoot());
  const doctorPath = path.join(installRoot, "scripts", "check_selfdex_setup.py");
  if (!fs.existsSync(doctorPath)) {
    fail(`setup doctor not found: ${doctorPath}. Run \`selfdex install\` first.`);
  }

  const python = resolvePython(options.python);
  if (!python) {
    fail("Python was not found. Install Python 3 or pass --python <path>.");
  }

  const doctorArgs = [
    ...python.slice(1),
    doctorPath,
    "--root",
    installRoot,
    "--format",
    options.format,
  ];
  if (options.home) {
    doctorArgs.push("--home", options.home);
  }
  if (options.codexHome) {
    doctorArgs.push("--codex-home", options.codexHome);
  }

  const result = spawnSync(python[0], doctorArgs, { stdio: "inherit" });
  if (result.error) {
    fail(result.error.message);
  }
  return result.status === null ? 1 : result.status;
}

function runDoctor(args) {
  const options = parseDoctorArgs(args);
  if (options.help) {
    printDoctorHelp();
    return 0;
  }

  if (options.python) {
    return runPythonDoctor(options);
  }

  const payload = buildNodeDoctorPayload(options);
  writeDoctorPayload(payload, options.format);
  return payload.status === "pass" ? 0 : 1;
}

function main(argv) {
  const [command, ...args] = argv;

  if (!command || command === "-h" || command === "--help") {
    printMainHelp();
    return 0;
  }

  if (command === "--version" || command === "version") {
    console.log(PACKAGE_JSON.version);
    return 0;
  }

  if (command === "install") {
    return runInstall(args);
  }

  if (command === "doctor") {
    return runDoctor(args);
  }

  fail(`unknown command: ${command}`);
}

process.exit(main(process.argv.slice(2)));
