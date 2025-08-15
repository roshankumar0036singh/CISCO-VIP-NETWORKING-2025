

import logging
import os
from pathlib import Path
from typing import Dict, Any
import networkx as nx


class topology_renderer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Path to assets folder relative to project root
        self.assets_dir = Path(__file__).parent.parent / "assets"
        if not self.assets_dir.exists():
            self.logger.warning(f"Assets folder not found: {self.assets_dir}")

        self.icon_map = {
            "router": "wifi-router.png",
            "pc": "monitor.png",
            "laptop": "laptop.png",
            "switch": "hub.png",
        }

        self.priority_colors = {
            "critical": "#8B0000",
            "high": "#FF6347",
            "medium": "#4682B4",
            "low": "#32CD32",
            "unknown": "#808080",
        }

    def render_interactive_topology(self, G: nx.Graph, output_file: Path):
        try:
            from pyvis.network import Network
        except ImportError:
            self.logger.error("pyvis is not installed. Run: pip install pyvis")
            raise

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Build PyVis graph (simple and stable)
        net = Network(
            height="900px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#000000",
            directed=False,
        )
        net.toggle_physics(True)

        # Nodes
        for nid, data in G.nodes(data=True):
            label = data.get("label", nid)
            title = data.get("title", label)
            device_type = (data.get("device_type") or "").lower()
            icon_key = data.get("device_icon", device_type if device_type in self.icon_map else "router")

            image_path = self._resolve_icon(icon_key, output_file.parent)
            if image_path:
                net.add_node(
                    nid,
                    label=label,
                    title=title,
                    shape="image",
                    image=image_path,
                    borderWidth=2,
                    color={"border": self._device_border_color(device_type)},
                )
            else:
                net.add_node(nid, label=label, title=title, shape="dot", size=18)

        # Edges
        for u, v, ed in G.edges(data=True):
            title = ed.get("title", f"{u} ↔ {v}")
            link_type = ed.get("link_type", "subnet")
            bandwidth_mbps = ed.get("bandwidth_mbps", 0.0)
            priority = ed.get("priority", "unknown")

            style = self._edge_style(link_type, bandwidth_mbps, priority)
            style["title"] = self._edge_title(title, ed)
            net.add_edge(u, v, **style)

        # 1) Generate PyVis HTML (this defines global `network`)
        pyvis_html = net.generate_html()

        # 2) Append controls AFTER `network` exists
        injection = self._controls_and_legend_html()
        final_html = self._inject_before_body_end(pyvis_html, injection)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_html)

        self.logger.info(f"Enhanced interactive topology saved to {output_file}")

    # ---------- Helpers ----------

    def _resolve_icon(self, icon_key: str, out_dir: Path) -> str | None:
        filename = self.icon_map.get(icon_key)
        if not filename:
            return None
        icon_path = self.assets_dir / filename
        if icon_path.is_file():
            try:
                return os.path.relpath(icon_path.resolve(), out_dir.resolve())
            except Exception:
                return str(icon_path.resolve())
        return None

    def _device_border_color(self, device_type: str) -> str:
        colors = {
            "router": "#c92a2a",
            "switch": "#1971c2",
            "pc": "#37b24d",
            "laptop": "#fab005",
        }
        return colors.get(device_type, "#666666")

    def _edge_style(self, link_type: str, bandwidth_mbps: float, priority: str) -> Dict[str, Any]:
        base = {
            "subnet": {"width": 3, "dashes": False},
            "ospf": {"width": 3, "dashes": [8, 4]},
            "bgp": {"width": 3, "dashes": [12, 6]},
            "description": {"width": 2, "dashes": [4, 4]},
        }.get(link_type, {"width": 3, "dashes": False})

        # Width by bandwidth
        if bandwidth_mbps >= 10000:
            base["width"] = max(base["width"], 6)
        elif bandwidth_mbps >= 1000:
            base["width"] = max(base["width"], 5)
        elif bandwidth_mbps < 100:
            base["width"] = max(base["width"] - 1, 1)

        base["color"] = self.priority_colors.get(priority, "#808080")

        if link_type == "bgp":
            base["arrows"] = {"to": {"enabled": True, "scaleFactor": 0.5}}

        return base

    def _edge_title(self, title: str, ed: Dict[str, Any]) -> str:
        bw = ed.get("bandwidth_mbps")
        util = ed.get("utilization_percent")
        prio = ed.get("priority")
        parts = [title]
        if bw is not None:
            parts.append(f"Bandwidth: {bw:.0f}Mbps")
        if util is not None:
            parts.append(f"Utilization: {util:.1f}%")
        if prio:
            parts.append(f"Priority: {prio}")
        return " | ".join(parts)

    def _inject_before_body_end(self, base_html: str, injection: str) -> str:
        idx = base_html.lower().rfind("</body>")
        if idx == -1:
            return base_html + injection
        return base_html[:idx] + injection + base_html[idx:]

    def _controls_and_legend_html(self) -> str:
        return """
<!-- Floating Controls and Legend (appended after PyVis created `network`) -->
<style>
  .floating-panel {
    position: fixed; bottom: 20px; left: 20px; z-index: 9999;
    background: #f8f9fa; border: 1px solid #ddd; padding: 10px 12px;
    border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,.12);
    font-family: Arial, sans-serif; font-size: 13px;
  }
  .floating-panel h4 { margin: 0 0 6px 0; font-size: 14px; }
  .floating-panel .row { margin-top: 6px; }
  .floating-panel button { margin-right: 8px; }
</style>
<div class="floating-panel">
  <h4>Controls</h4>
  <div class="row">
    <button id="fitBtn">Fit to Screen</button>
    <button id="togglePhysicsBtn">Toggle Physics</button>
  </div>
  <div class="row" style="margin-top:8px;">
    <strong>Link Types:</strong>
    <span style="margin-left:6px;">— Subnet</span>
    <span style="margin-left:6px; border-bottom:2px dashed #000;">— OSPF</span>
    <span style="margin-left:6px; border-bottom:2px dashed #000;">— BGP</span>
  </div>
</div>

<script>
(function() {
  function wireUp() {
    try {
      if (typeof network === "undefined") {
        // PyVis hasn't created it yet; try again shortly
        return setTimeout(wireUp, 50);
      }
      var physicsEnabled = true;

      var fitBtn = document.getElementById("fitBtn");
      if (fitBtn) {
        fitBtn.addEventListener("click", function() {
          try { network.fit(); } catch (e) { console.warn("fit() failed:", e); }
        });
      }

      var toggleBtn = document.getElementById("togglePhysicsBtn");
      if (toggleBtn) {
        toggleBtn.addEventListener("click", function() {
          physicsEnabled = !physicsEnabled;
          try { network.setOptions({ physics: { enabled: physicsEnabled } }); }
          catch (e) { console.warn("toggle physics failed:", e); }
        });
      }
    } catch (e) {
      console.warn("Control wiring error:", e);
      setTimeout(wireUp, 100);
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireUp);
  } else {
    wireUp();
  }
})();
</script>
"""
