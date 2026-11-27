# 席→模型档位映射表（CEO 令 2026-11-27 16:11·席位模型分工落地）
# 用途：launch-seat.ps1 / launch-m-cos.ps1 按席查本表取 --model 档位（别名非字面模型名）
# 目标机：本机（M 面本地）
# 触发方式：启动器运行时读取（sync.ps1 单向维护部署位）
# 真源位：TriCompany/scripts/ops/launch/seat-model-map.psd1
#
# 改分工=只改本表·不动启动器脚本。
# 档位=别名（settings.json 集中映射·--model 跟别名走）：opus=glm-5.4｜sonnet=glm-5.3-flash
#   · 必用 glm-5.4：m-cos、m-cto、m-cpo、m-coo → opus
#   · 用 glm-5.3-flash：bod 与执行席（m-fsd、m-ste、m-pm、m-rdt、m-sde）→ sonnet
#   · 其余 C-level（m-cao、m-cho、m-cfo、m-cmo、m-cso）：候 CFO 评估·评估前按 flash → sonnet
# 表里没有的席=Default 档（sonnet）

@{
    Default = 'sonnet'
    Seats   = @{
        'm-cos' = 'opus'
        'm-cto' = 'opus'
        'm-cpo' = 'opus'
        'm-coo' = 'opus'
        'm-fsd' = 'sonnet'
        'm-ste' = 'sonnet'
        'm-pm'  = 'sonnet'
        'm-rdt' = 'sonnet'
        'm-sde' = 'sonnet'
        'm-cao' = 'sonnet'
        'm-cho' = 'sonnet'
        'm-cfo' = 'sonnet'
        'm-cmo' = 'sonnet'
        'm-cso' = 'sonnet'
    }
}
