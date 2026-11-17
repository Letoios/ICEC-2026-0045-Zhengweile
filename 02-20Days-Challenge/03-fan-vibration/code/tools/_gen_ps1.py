# -*- coding: utf-8 -*-
r"""生成 D:\deepseek工作\入库_项目三.ps1（带 UTF-8 BOM，PowerShell 5.1 才不会乱码）。"""
import io, os

PS = r'''# 项目三 入库脚本（阶段二 20 天挑战）
# 用法：powershell -ExecutionPolicy Bypass -File "D:\deepseek工作\入库_项目三.ps1"

$ErrorActionPreference = "Stop"
$src  = "D:\deepseek工作\proj03"
$repo = "D:\ICEC-2026-0045-Zhengweile"
$dst  = Join-Path $repo "02-20Days-Challenge\03-fan-vibration"

Write-Host "=== 1/4 检查路径 ===" -ForegroundColor Cyan
if (-not (Test-Path $src))  { throw "源目录不存在：$src" }
if (-not (Test-Path $repo)) { throw "仓库不存在：$repo" }

Write-Host "=== 2/4 重建目标目录 ===" -ForegroundColor Cyan
if (Test-Path $dst) {
    Write-Host "目标已存在，先清空：$dst"
    Remove-Item $dst -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $dst | Out-Null

Write-Host "=== 3/4 复制（跳过 __pycache__ / .pyc / 临时脚本）===" -ForegroundColor Cyan
$copied = 0
$bytes  = 0
Get-ChildItem $src -Recurse -File | Where-Object {
    $_.FullName -notmatch "\\__pycache__\\" -and
    $_.Extension -ne ".pyc" -and
    $_.Name -notmatch "^_"
} | ForEach-Object {
    $rel = $_.FullName.Substring($src.Length + 1)
    $out = Join-Path $dst $rel
    $dir = Split-Path $out -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    Copy-Item $_.FullName $out -Force
    $copied++
    $bytes += $_.Length
}
Write-Host ("复制完成：{0} 个文件，{1:N1} MB" -f $copied, ($bytes / 1MB)) -ForegroundColor Green

Write-Host "=== 4/4 目录结构 ===" -ForegroundColor Cyan
Get-ChildItem $dst -Directory | ForEach-Object {
    $n = (Get-ChildItem $_.FullName -Recurse -File).Count
    Write-Host ("  [目录] {0}  ({1} 个文件)" -f $_.Name, $n)
}
$rootFiles = (Get-ChildItem $dst -File).Count
if ($rootFiles -gt 0) { Write-Host ("  [文件] 根目录 {0} 个" -f $rootFiles) }

Write-Host ""
Write-Host "=== 下一步：在仓库里提交并推送 ===" -ForegroundColor Yellow
Write-Host "cd $repo"
Write-Host "git status"
Write-Host 'git add "02-20Days-Challenge/03-fan-vibration"'
Write-Host 'git commit -m "项目三：基于手机声学的旋转机械异常诊断（98 段、五工况、三类 90.8%）"'
Write-Host "git push"
Write-Host ""
Write-Host "注意：不要用 git add -A（06/08 那边可能还有未提交改动）" -ForegroundColor Red
'''

path = r"D:\deepseek工作\入库_项目三.ps1"
with io.open(path, "w", encoding="utf-8-sig", newline="\r\n") as f:
    f.write(PS)

# 语法校验
import subprocess
r = subprocess.run([
    "powershell", "-NoProfile", "-Command",
    "$e=$null;[void][System.Management.Automation.Language.Parser]::ParseFile('%s',[ref]$null,[ref]$e);"
    "if($e){$e|%%{'ERR '+$_.Message}}else{'语法 OK'}" % path.replace("\\", "\\\\")
], capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip())
print("写入：", path, os.path.getsize(path), "bytes")
