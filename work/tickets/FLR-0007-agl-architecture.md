# FLR-0007 — Map the AGL assembly process for Fluorite

- Status: Next
- Priority: High
- Depends on: FLR-0001
- Context: [rendering stack](../context/fluorite-rendering-stack.md)

## Purpose

AGLがfixed manifestからimage、compositor、ivi launcher、Flutter bundleをどのlayer/recipe/configで組み立てるか説明可能にする。

## Stratification — 4W1H excluding Why

| Dimension | Initial stratum |
| --- | --- |
| What | layer、image recipe、packagegroup、launcher recipe、app recipe |
| Where | meta-agl、meta-agl-demo、meta-flutter、custom layer |
| When | parse、fetch、configure、compile、package、rootfs、boot |
| Who | recipe/class/package role |
| How | inherit、DEPENDS/RDEPENDS、PACKAGECONFIG、override、image install |

## Success criteria

- imageからFluorite packageまでのrecipe dependency pathを示す。
- active bbappend、class、overrideと採用理由を実効値で示す。
- source revisionとbinary package provenanceを結ぶ。
- AGL固有部分とupstream Yocto部分を分離する。

## Process analysis target

manifest → layer selection → image recipe → packagegroup → launcher/app recipes → rootfs → systemd/compositor startup。
