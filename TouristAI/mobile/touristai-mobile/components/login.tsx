// app/index.tsx  (Expo Router)  — or rename to App.tsx for classic Expo
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
  Alert,
  StatusBar,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

/**
 * Tourist.AI — ChatGPT-style login screen
 * Theme: deep navy background + teal/cyan accent (matches Tourist.AI UI)
 */

const COLORS = {
  bg: "#0B1220",           // deep navy background
  surface: "#111A2E",      // card / input background
  border: "#1F2A44",       // subtle border
  text: "#E6EDF7",         // primary text
  muted: "#8A97B1",        // secondary text
  accent: "#14B8A6",       // teal (Tourist.AI brand)
  accentSoft: "#0EA5A4",
  danger: "#EF4444",
  white: "#FFFFFF",
};

// export default function LoginScreen() {
export default function LoginScreen({
  onLogin,
}: {
  onLogin: () => void;
}){
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const isSignup = mode === "signup";

  const handleSubmit = async () => {
    if (!email.trim() || !password) {
      Alert.alert("Missing info", "Please enter your email and password.");
      return;
    }
    setLoading(true);
    try {
      // TODO: Wire this to your backend (e.g. axios.post(`${API}/auth/login`, {...}))
      await new Promise((r) => setTimeout(r, 900));
      // Alert.alert(
      //   isSignup ? "Account created" : "Welcome back",
      //   `Signed in as ${email}`
      // );
      onLogin();
    } catch (e: any) {
      Alert.alert("Error", e?.message ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const socialBtn = (
    icon: keyof typeof Ionicons.glyphMap,
    label: string,
    onPress: () => void
  ) => (
    <TouchableOpacity style={styles.socialBtn} onPress={onPress} activeOpacity={0.8}>
      <Ionicons name={icon} size={20} color={COLORS.text} />
      <Text style={styles.socialText}>{label}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.bg} />
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Logo */}
          <View style={styles.logoWrap}>
            <View style={styles.logoCircle}>
              <Ionicons name="compass" size={34} color={COLORS.white} />
            </View>
            <Text style={styles.brand}>Tourist.AI</Text>
            <Text style={styles.tagline}>Discover. Plan. Explore.</Text>
          </View>

          {/* Heading */}
          <Text style={styles.title}>
            {isSignup ? "Create your account" : "Welcome back"}
          </Text>
          <Text style={styles.subtitle}>
            {isSignup
              ? "Sign up to start planning smarter trips."
              : "Log in to continue your journey."}
          </Text>

          {/* Email */}
          <View style={styles.inputWrap}>
            <Ionicons name="mail-outline" size={18} color={COLORS.muted} />
            <TextInput
              style={styles.input}
              placeholder="Email address"
              placeholderTextColor={COLORS.muted}
              autoCapitalize="none"
              keyboardType="email-address"
              value={email}
              onChangeText={setEmail}
            />
          </View>

          {/* Password */}
          <View style={styles.inputWrap}>
            <Ionicons name="lock-closed-outline" size={18} color={COLORS.muted} />
            <TextInput
              style={styles.input}
              placeholder="Password"
              placeholderTextColor={COLORS.muted}
              secureTextEntry={!showPw}
              value={password}
              onChangeText={setPassword}
            />
            <TouchableOpacity onPress={() => setShowPw((s) => !s)}>
              <Ionicons
                name={showPw ? "eye-off-outline" : "eye-outline"}
                size={18}
                color={COLORS.muted}
              />
            </TouchableOpacity>
          </View>

          {!isSignup && (
            <TouchableOpacity style={styles.forgot}>
              <Text style={styles.forgotText}>Forgot password?</Text>
            </TouchableOpacity>
          )}

          {/* Primary CTA */}
          <TouchableOpacity
            style={[styles.primaryBtn, loading && { opacity: 0.7 }]}
            onPress={handleSubmit}
            disabled={loading}
            activeOpacity={0.9}
          >
            {loading ? (
              <ActivityIndicator color={COLORS.white} />
            ) : (
              <Text style={styles.primaryText}>
                {isSignup ? "Sign up" : "Continue"}
              </Text>
            )}
          </TouchableOpacity>

          {/* Switch mode */}
          <View style={styles.switchRow}>
            <Text style={styles.muted}>
              {isSignup ? "Already have an account?" : "Don't have an account?"}
            </Text>
            <TouchableOpacity
              onPress={() => setMode(isSignup ? "login" : "signup")}
            >
              <Text style={styles.link}>
                {isSignup ? " Log in" : " Sign up"}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Divider */}
          <View style={styles.divider}>
            <View style={styles.line} />
            <Text style={styles.dividerText}>OR</Text>
            <View style={styles.line} />
          </View>

          {/* Social */}
          {socialBtn("logo-google", "Continue with Google", () =>
            Alert.alert("Google", "Hook up Google OAuth here")
          )}
          {socialBtn("logo-apple", "Continue with Apple", () =>
            Alert.alert("Apple", "Hook up Apple OAuth here")
          )}
          {socialBtn("phone-portrait-outline", "Continue with phone", () =>
            Alert.alert("Phone", "Hook up phone OTP here")
          )}

          {/* Footer */}
          <Text style={styles.footer}>
            By continuing, you agree to Tourist.AI's{" "}
            <Text style={styles.link}>Terms</Text> &{" "}
            <Text style={styles.link}>Privacy Policy</Text>.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: COLORS.bg },
  scroll: { padding: 24, paddingTop: 60, paddingBottom: 40 },

  logoWrap: { alignItems: "center", marginBottom: 32 },
  logoCircle: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: COLORS.accent,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: COLORS.accent,
    shadowOpacity: 0.4,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 8 },
    elevation: 6,
  },
  brand: {
    marginTop: 14,
    color: COLORS.text,
    fontSize: 22,
    fontWeight: "700",
    letterSpacing: 0.3,
  },
  tagline: { color: COLORS.muted, fontSize: 13, marginTop: 4 },

  title: {
    color: COLORS.text,
    fontSize: 26,
    fontWeight: "700",
    textAlign: "center",
    marginTop: 8,
  },
  subtitle: {
    color: COLORS.muted,
    fontSize: 14,
    textAlign: "center",
    marginTop: 6,
    marginBottom: 28,
  },

  inputWrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    paddingHorizontal: 14,
    height: 52,
    marginBottom: 12,
  },
  input: {
    flex: 1,
    color: COLORS.text,
    fontSize: 15,
    paddingVertical: 0,
  },

  forgot: { alignSelf: "flex-end", marginTop: 2, marginBottom: 16 },
  forgotText: { color: COLORS.accent, fontSize: 13, fontWeight: "500" },

  primaryBtn: {
    backgroundColor: COLORS.accent,
    height: 52,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 6,
    shadowColor: COLORS.accent,
    shadowOpacity: 0.35,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 4,
  },
  primaryText: { color: COLORS.white, fontSize: 16, fontWeight: "600" },

  switchRow: {
    flexDirection: "row",
    justifyContent: "center",
    marginTop: 18,
  },
  muted: { color: COLORS.muted, fontSize: 14 },
  link: { color: COLORS.accent, fontSize: 14, fontWeight: "600" },

  divider: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 24,
    gap: 12,
  },
  line: { flex: 1, height: 1, backgroundColor: COLORS.border },
  dividerText: { color: COLORS.muted, fontSize: 12, letterSpacing: 1 },

  socialBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    height: 50,
    borderRadius: 14,
    marginBottom: 10,
  },
  socialText: { color: COLORS.text, fontSize: 15, fontWeight: "500" },

  footer: {
    color: COLORS.muted,
    fontSize: 12,
    textAlign: "center",
    marginTop: 24,
    lineHeight: 18,
  },
});


