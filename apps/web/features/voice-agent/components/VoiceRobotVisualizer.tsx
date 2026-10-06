"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface VoiceRobotVisualizerProps {
  status: "disconnected" | "connecting" | "connected" | "tutor-speaking" | "agent-speaking" | "error";
  isMuted?: boolean;
}

export const VoiceRobotVisualizer: React.FC<VoiceRobotVisualizerProps> = ({
  status,
  isMuted = false,
}) => {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const statusRef = useRef(status);
  const isMutedRef = useRef(isMuted);

  useEffect(() => {
    statusRef.current = status;
    isMutedRef.current = isMuted;
  }, [status, isMuted]);

  useEffect(() => {
    const mountEl = mountRef.current;
    if (!mountEl) return;

    // Dimensions
    const width = mountEl.clientWidth || 320;
    const height = mountEl.clientHeight || 320;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.z = 4.2;

    // 2. WebGL Renderer
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      mountEl.appendChild(renderer.domElement);
    } catch (e) {
      console.warn("WebGL initialization failed:", e);
      return;
    }

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(5, 5, 5);
    scene.add(dirLight);

    const pointLight = new THREE.PointLight(0x9b6ef8, 2.5, 10);
    pointLight.position.set(0, 0, 1.5);
    scene.add(pointLight);

    // 4. Robot Group
    const robotGroup = new THREE.Group();
    scene.add(robotGroup);

    // Head: Wireframe Icosahedron
    const headGeo = new THREE.IcosahedronGeometry(1.2, 1);
    const headMat = new THREE.MeshPhongMaterial({
      color: 0x4f46e5,
      wireframe: true,
      emissive: 0x312e81,
      emissiveIntensity: 0.6,
      transparent: true,
      opacity: 0.85,
    });
    const head = new THREE.Mesh(headGeo, headMat);
    robotGroup.add(head);

    // Inner Glowing Core Sphere
    const coreGeo = new THREE.SphereGeometry(0.55, 32, 32);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.95,
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    robotGroup.add(core);

    // Outer Halo Ring
    const ringGeo = new THREE.TorusGeometry(1.5, 0.02, 16, 100);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      transparent: true,
      opacity: 0.35,
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2.3;
    robotGroup.add(ring);

    // 5. Animation Loop
    const clock = new THREE.Clock();
    let animationId: number;

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      const currentStatus = statusRef.current;
      const muted = isMutedRef.current;

      // Color and visual responsiveness based on conversation state
      if (currentStatus === "tutor-speaking" || currentStatus === "agent-speaking") {
        headMat.color.setHex(0x9b6ef8); // Purple
        headMat.emissive.setHex(0x5b21b6);
        pointLight.color.setHex(0x9b6ef8);
        ringMat.color.setHex(0xa855f7);

        // Core pulsing rapidly while speaking
        const pulse = 1 + Math.sin(t * 8) * 0.25;
        core.scale.set(pulse, pulse, pulse);
        head.rotation.y += 0.02;
        head.rotation.x = Math.sin(t * 2) * 0.08;
      } else if (currentStatus === "connected") {
        if (muted) {
          headMat.color.setHex(0xef4444); // Muted red
          headMat.emissive.setHex(0x7f1d1d);
          pointLight.color.setHex(0xef4444);
        } else {
          headMat.color.setHex(0x39ff14); // Neon Green Listening
          headMat.emissive.setHex(0x065f46);
          pointLight.color.setHex(0x34d399);
        }
        ringMat.color.setHex(0x10b981);

        // Gentle breathing pulse
        const pulse = 1 + Math.sin(t * 2.5) * 0.08;
        core.scale.set(pulse, pulse, pulse);
        head.rotation.y += 0.008;
        head.rotation.x = Math.sin(t * 1.2) * 0.04;
      } else if (currentStatus === "connecting") {
        headMat.color.setHex(0xfbbf24); // Amber
        headMat.emissive.setHex(0x78350f);
        pointLight.color.setHex(0xf59e0b);
        ringMat.color.setHex(0xfbbf24);

        const pulse = 1 + Math.sin(t * 5) * 0.15;
        core.scale.set(pulse, pulse, pulse);
        head.rotation.y += 0.03;
      } else if (currentStatus === "error") {
        headMat.color.setHex(0xef4444); // Red
        headMat.emissive.setHex(0x991b1b);
        pointLight.color.setHex(0xef4444);
        core.scale.set(0.9, 0.9, 0.9);
      } else {
        // Disconnected / Idle
        headMat.color.setHex(0x4f46e5); // Indigo
        headMat.emissive.setHex(0x1e1b4b);
        pointLight.color.setHex(0x4f46e5);
        ringMat.color.setHex(0x6366f1);

        const pulse = 1 + Math.sin(t * 1.5) * 0.04;
        core.scale.set(pulse, pulse, pulse);
        head.rotation.y += 0.005;
      }

      // Gentle floating bob
      robotGroup.position.y = Math.sin(t * 1.6) * 0.12;
      ring.rotation.z = t * 0.2;

      renderer.render(scene, camera);
    };

    animate();

    // 6. Handle Resizing
    const handleResize = () => {
      if (!mountEl || !renderer) return;
      const newWidth = mountEl.clientWidth || 320;
      const newHeight = mountEl.clientHeight || 320;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };

    window.addEventListener("resize", handleResize);

    // 7. Cleanup
    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", handleResize);

      try {
        mountEl.removeChild(renderer.domElement);
        renderer.dispose();
        headGeo.dispose();
        headMat.dispose();
        coreGeo.dispose();
        coreMat.dispose();
        ringGeo.dispose();
        ringMat.dispose();
      } catch (_) {}
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
      }}
    />
  );
};
