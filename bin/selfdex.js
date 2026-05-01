#!/usr/bin/env node

"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const INSTALLER_PATH = path.join(PACKAGE_ROOT, "install.ps1");
const PACKAGE_JSON = require(path.join(PACKAGE_ROOT, "package.json"));

function printMainHelp() {
  console.log(`Selfdex ${PACKAGE_JSON.version}

Usage:
  selfdex install [options]
  selfdex --help
  selfdex --version

Commands:
  install    Clone or update Selfdex, then install the @selfdex Codex plugin.

Install options:
  --dry-run                 Show what would happen without cloning or installing.
  --install-root <path>     Selfdex checkout path. Defaults to $HOME/selfdex.
  --repo-url <url>          Git repository URL used by the bootstrap installer.
  --branch <name>           Git branch used by the bootstrap installer.
  --skip-plugin-install     Clone or update Selfdex without installing @selfdex.
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
  --repo-url <url>          Git repository URL used by the bootstrap installer.
  --branch <name>           Git branch used by the bootstrap installer.
  --skip-plugin-install     Clone or update Selfdex without installing @selfdex.
  --python <path>           Python executable used by the plugin installer.
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
    repoUrl: null,
    branch: null,
    skipPluginInstall: false,
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
  if (options.python) {
    args.push("-Python", options.python);
  }
  if (options.dryRun) {
    args.push("-DryRun");
  }
  if (options.skipPluginInstall) {
    args.push("-SkipPluginInstall");
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

  fail(`unknown command: ${command}`);
}

process.exit(main(process.argv.slice(2)));
