#!/usr/bin/env node

"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const PACKAGE_JSON = require(path.join(PACKAGE_ROOT, "package.json"));
const DEFAULT_REPO_URL = "https://github.com/r2gul4r/selfdex.git";
const DEFAULT_BRANCH = "main";
const PLUGIN_NAME = "selfdex";
const PLUGIN_REL = ["plugins", PLUGIN_NAME];
const PLUGIN_JSON_REL = [...PLUGIN_REL, ".codex-plugin", "plugin.json"];
const SKILL_REL = [...PLUGIN_REL, "skills", PLUGIN_NAME, "SKILL.md"];
const GLOBAL_SKILL_REL = ["skills", PLUGIN_NAME];
const MARKETPLACE_REL = [".agents", "plugins", "marketplace.json"];
const ROOT_CONFIG_NAME = "selfdex-root.json";

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
  --repo-url <url>          Git repository URL used by the installer.
  --branch <name>           Git branch used by the installer.
  --use-existing-checkout   Use --install-root as-is without clone/update.
  --skip-plugin-install     Clone or update Selfdex without installing @selfdex.
  --skip-doctor             Do not run the setup doctor after install.
  --python <path>           Accepted for legacy script compatibility; ignored by Node-native install.
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
  --repo-url <url>          Git repository URL used by the installer.
  --branch <name>           Git branch used by the installer.
  --use-existing-checkout   Use --install-root as-is without clone/update.
  --skip-plugin-install     Clone or update Selfdex without installing @selfdex.
  --skip-doctor             Do not run the setup doctor after install.
  --python <path>           Accepted for legacy script compatibility; ignored by Node-native install.
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
    useExistingCheckout: false,
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
      case "--use-existing-checkout":
        options.useExistingCheckout = true;
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

function writeJsonFile(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
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

function isDirectoryEmpty(dirPath) {
  try {
    return fs.readdirSync(dirPath).length === 0;
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return true;
    }
    throw error;
  }
}

function runProcess(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd,
    stdio: options.stdio || "inherit",
    encoding: options.encoding || "utf8",
  });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    const rendered = [command, ...args].join(" ");
    throw new Error(`${rendered} failed with exit code ${result.status}`);
  }
  return result;
}

function writeStep(message) {
  console.log(`[selfdex] ${message}`);
}

function sourcePath(root, relPath) {
  return path.join(root, ...relPath);
}

function validateInstallSource(root) {
  const findings = [];
  const requiredPaths = [
    PLUGIN_JSON_REL,
    SKILL_REL,
    ["scripts", "plan_external_project.py"],
    ["scripts", "run_target_codex.py"],
    ["CAMPAIGN_STATE.json"],
  ];
  for (const relPath of requiredPaths) {
    const target = sourcePath(root, relPath);
    if (!pathExists(target)) {
      findings.push({
        finding_id: "missing-source-file",
        severity: "high",
        path: relPath.join("/"),
        summary: "Required Selfdex installer source file is missing.",
      });
    }
  }
  const pluginJsonPath = sourcePath(root, PLUGIN_JSON_REL);
  if (pathExists(pluginJsonPath)) {
    try {
      const plugin = readJsonFile(pluginJsonPath);
      if (plugin.name !== PLUGIN_NAME) {
        findings.push({
          finding_id: "plugin-name-mismatch",
          severity: "high",
          path: PLUGIN_JSON_REL.join("/"),
          summary: "Source plugin manifest name must be selfdex.",
        });
      }
    } catch (error) {
      findings.push({
        finding_id: "invalid-plugin-manifest",
        severity: "high",
        path: PLUGIN_JSON_REL.join("/"),
        summary: `Source plugin manifest could not be read: ${error.message}`,
      });
    }
  }
  return findings;
}

function marketplaceEntry(sourcePathValue) {
  return {
    name: PLUGIN_NAME,
    source: {
      source: "local",
      path: sourcePathValue,
    },
    policy: {
      installation: "AVAILABLE",
      authentication: "ON_INSTALL",
    },
    category: "Productivity",
  };
}

function loadMarketplace(marketplacePath) {
  if (!pathExists(marketplacePath)) {
    return {
      name: "selfdex-local",
      interface: {
        displayName: "Selfdex Local",
      },
      plugins: [],
    };
  }
  const payload = readJsonFile(marketplacePath);
  if (!Array.isArray(payload.plugins)) {
    throw new Error(`${marketplacePath} field 'plugins' must be an array`);
  }
  if (payload.interface && typeof payload.interface !== "object") {
    throw new Error(`${marketplacePath} field 'interface' must be an object`);
  }
  if (!payload.interface) {
    payload.interface = { displayName: "Selfdex Local" };
  }
  return payload;
}

function updateMarketplace(payload, sourcePathValue) {
  const desired = marketplaceEntry(sourcePathValue);
  const index = payload.plugins.findIndex((entry) => entry && entry.name === PLUGIN_NAME);
  if (index === -1) {
    payload.plugins.push(desired);
    return "marketplace_entry_added";
  }
  if (JSON.stringify(payload.plugins[index]) === JSON.stringify(desired)) {
    return "marketplace_entry_current";
  }
  payload.plugins[index] = desired;
  return "marketplace_entry_replaced";
}

function relativePluginSource(home, targetPlugin) {
  const rel = path.relative(path.resolve(home), path.resolve(targetPlugin));
  if (!rel || rel.startsWith("..") || path.isAbsolute(rel)) {
    throw new Error("Target plugin path must be inside the selected plugin home directory");
  }
  return `./${rel.split(path.sep).join("/")}`;
}

function listFilesRecursive(root) {
  const files = [];
  if (!pathExists(root)) {
    return files;
  }
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const entryPath = path.join(root, entry.name);
    if (entry.isDirectory()) {
      files.push(...listFilesRecursive(entryPath));
    } else if (entry.isFile()) {
      files.push(entryPath);
    }
  }
  return files.sort();
}

function copyFilePreservingDirs(sourceRoot, targetRoot, sourceFile) {
  const rel = path.relative(sourceRoot, sourceFile);
  const targetFile = path.join(targetRoot, rel);
  fs.mkdirSync(path.dirname(targetFile), { recursive: true });
  fs.copyFileSync(sourceFile, targetFile);
  return targetFile;
}

function appendInstalledCheckout(skillPath, selfdexRoot) {
  let text = fs.readFileSync(skillPath, "utf8");
  const marker = "## Installed Checkout";
  const markerIndex = text.indexOf(marker);
  if (markerIndex !== -1) {
    text = `${text.slice(0, markerIndex).trimEnd()}\n`;
  }
  const nextText = `${text.trimEnd()}\n\n${marker}\n\nThis plugin was installed from this Selfdex checkout:\n\n\`${selfdexRoot}\`\n`;
  fs.writeFileSync(skillPath, nextText, "utf8");
}

function copyPluginFiles(sourcePlugin, targetPlugin, selfdexRoot) {
  let count = 0;
  for (const sourceFile of listFilesRecursive(sourcePlugin)) {
    copyFilePreservingDirs(sourcePlugin, targetPlugin, sourceFile);
    count += 1;
  }
  writeJsonFile(path.join(targetPlugin, ROOT_CONFIG_NAME), {
    schema_version: 1,
    selfdex_root: selfdexRoot,
  });
  appendInstalledCheckout(path.join(targetPlugin, "skills", PLUGIN_NAME, "SKILL.md"), selfdexRoot);
  return count + 1;
}

function copyGlobalSkillFiles(sourceSkill, targetSkill, selfdexRoot) {
  let count = 0;
  for (const sourceFile of listFilesRecursive(sourceSkill)) {
    copyFilePreservingDirs(sourceSkill, targetSkill, sourceFile);
    count += 1;
  }
  appendInstalledCheckout(path.join(targetSkill, "SKILL.md"), selfdexRoot);
  return count;
}

function buildInstallPayload(root, home, options = {}) {
  const resolvedRoot = path.resolve(root);
  const resolvedHome = path.resolve(home);
  const sourcePlugin = path.join(resolvedRoot, ...PLUGIN_REL);
  const sourceSkill = path.join(resolvedRoot, ...PLUGIN_REL, "skills", PLUGIN_NAME);
  const targetPlugin = path.join(resolvedHome, "plugins", PLUGIN_NAME);
  const targetSkill = path.join(resolvedHome, ...GLOBAL_SKILL_REL);
  const marketplacePath = path.join(resolvedHome, ...MARKETPLACE_REL);
  const dryRun = Boolean(options.dryRun);
  const findings = validateInstallSource(resolvedRoot);

  if (normalizePathForCompare(sourcePlugin) === normalizePathForCompare(targetPlugin)) {
    findings.push({
      finding_id: "source-target-overlap",
      severity: "high",
      path: targetPlugin,
      summary: "Install target must not be the source plugin directory; choose a real home directory.",
    });
  }

  const marketplaceSourcePath = relativePluginSource(resolvedHome, targetPlugin);
  let marketplaceStatus = "marketplace_entry_blocked";
  let marketplace = null;
  if (findings.length === 0) {
    marketplace = loadMarketplace(marketplacePath);
    marketplaceStatus = updateMarketplace(marketplace, marketplaceSourcePath);
  }

  const operationStatus = dryRun && findings.length === 0 ? "planned" : findings.length > 0 ? "blocked" : "ready";
  const operations = [
    {
      action: "copy_plugin",
      source: sourcePlugin,
      target: targetPlugin,
      status: operationStatus,
    },
    {
      action: "write_root_config",
      target: path.join(targetPlugin, ROOT_CONFIG_NAME),
      status: operationStatus,
    },
    {
      action: "copy_global_skill",
      source: sourceSkill,
      target: targetSkill,
      status: operationStatus,
    },
    {
      action: "update_marketplace",
      target: marketplacePath,
      status: findings.length > 0 ? "blocked" : dryRun ? "planned" : marketplaceStatus,
    },
  ];

  let filesCopied = 0;
  if (findings.length === 0 && !dryRun) {
    filesCopied += copyPluginFiles(sourcePlugin, targetPlugin, resolvedRoot);
    filesCopied += copyGlobalSkillFiles(sourceSkill, targetSkill, resolvedRoot);
    writeJsonFile(marketplacePath, marketplace);
    for (const operation of operations) {
      if (operation.status === "ready" || operation.status === marketplaceStatus) {
        operation.status = "done";
      }
    }
  }

  return {
    schema_version: 1,
    analysis_kind: "selfdex_plugin_install",
    runtime: "node-native",
    status: findings.length === 0 ? "pass" : "fail",
    dry_run: dryRun,
    writes_enabled: !dryRun,
    root: resolvedRoot,
    home: resolvedHome,
    source_plugin: sourcePlugin,
    source_skill: sourceSkill,
    target_plugin: targetPlugin,
    target_skill: targetSkill,
    marketplace_path: marketplacePath,
    marketplace_source_path: marketplaceSourcePath,
    operation_count: operations.length,
    operations,
    files_copied: filesCopied,
    finding_count: findings.length,
    findings,
    next_step:
      !dryRun && findings.length === 0
        ? "Restart or refresh Codex plugin discovery, then invoke @selfdex from a target project session."
        : "Rerun without --dry-run to install, or fix the findings first.",
  };
}

function checkoutSelfdex(options) {
  const installRoot = path.resolve(options.installRoot || defaultInstallRoot());
  const repoUrl = options.repoUrl || DEFAULT_REPO_URL;
  const branch = options.branch || DEFAULT_BRANCH;

  if (options.useExistingCheckout) {
    if (!pathExists(installRoot)) {
      fail(`existing checkout not found: ${installRoot}`);
    }
    writeStep("using existing checkout without clone/update");
    return installRoot;
  }

  if (!commandExists("git")) {
    fail("Missing required command for cloning or updating Selfdex. Tried: git.");
  }

  const gitDir = path.join(installRoot, ".git");
  if (pathExists(gitDir)) {
    writeStep("updating existing checkout");
    runProcess("git", ["-C", installRoot, "fetch", "origin", branch]);
    runProcess("git", ["-C", installRoot, "checkout", branch]);
    runProcess("git", ["-C", installRoot, "pull", "--ff-only", "origin", branch]);
    return installRoot;
  }

  if (pathExists(installRoot) && !isDirectoryEmpty(installRoot)) {
    fail(`Install root exists but is not an empty Selfdex git checkout: ${installRoot}`);
  }

  writeStep(pathExists(installRoot) ? "cloning into existing empty directory" : "cloning Selfdex");
  runProcess("git", ["clone", "--branch", branch, repoUrl, installRoot]);
  return installRoot;
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

function runInstall(args) {
  const options = parseInstallArgs(args);
  if (options.help) {
    printInstallHelp();
    return 0;
  }

  const installRoot = path.resolve(options.installRoot || defaultInstallRoot());
  const pluginHome = path.resolve(options.pluginHome || defaultCodexHome());
  const repoUrl = options.repoUrl || DEFAULT_REPO_URL;
  const branch = options.branch || DEFAULT_BRANCH;

  writeStep("runtime: node-native install");
  writeStep(`repo: ${repoUrl}`);
  writeStep(`branch: ${branch}`);
  writeStep(`install root: ${installRoot}`);
  writeStep(`plugin home: ${pluginHome}`);
  if (options.python) {
    writeStep("--python is ignored by the Node-native install path; legacy scripts may still accept it.");
  }

  if (options.dryRun) {
    writeStep("dry run: no clone, update, plugin install, or doctor check will run");
    writeStep(
      options.useExistingCheckout
        ? "would use the existing Selfdex checkout without clone/update"
        : "would clone Selfdex if missing, or pull --ff-only if already present"
    );
    if (!options.skipPluginInstall) {
      let installPayload;
      try {
        installPayload = buildInstallPayload(installRoot, pluginHome, { dryRun: true });
      } catch (error) {
        fail(error.message);
      }
      for (const operation of installPayload.operations) {
        writeStep(`would ${operation.action}: ${operation.target}`);
      }
    }
    if (!options.skipPluginInstall && !options.skipDoctor) {
      writeStep("would run Node-native selfdex doctor after plugin install");
    }
    return 0;
  }

  let checkoutRoot;
  try {
    checkoutRoot = checkoutSelfdex(options);
  } catch (error) {
    fail(error.message);
  }
  if (options.skipPluginInstall) {
    writeStep("skipped plugin install");
    return 0;
  }

  writeStep("installing @selfdex plugin");
  let installPayload;
  try {
    installPayload = buildInstallPayload(checkoutRoot, pluginHome, { dryRun: false });
  } catch (error) {
    fail(error.message);
  }
  if (installPayload.status !== "pass") {
    for (const finding of installPayload.findings) {
      console.error(`[selfdex] ${finding.finding_id}: ${finding.path}: ${finding.summary}`);
    }
    return 1;
  }
  writeStep(`installed plugin files: ${installPayload.files_copied}`);

  if (!options.skipDoctor) {
    writeStep("checking setup");
    const doctorPayload = buildNodeDoctorPayload({
      installRoot: checkoutRoot,
      home: pluginHome,
      codexHome: pluginHome,
      format: "markdown",
    });
    writeDoctorPayload(doctorPayload, "markdown");
    if (doctorPayload.status !== "pass") {
      return 1;
    }
  }

  writeStep("done. Restart or refresh Codex plugin discovery, then call @selfdex from a target project session.");
  return 0;
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
