import React from "react";
import { motion } from "framer-motion";
import { 
  Code2, 
  Map, 
  Share2, 
  Book, 
  Users, 
  ArrowRight, 
  Github, 
  LineChart, 
  Globe 
} from "lucide-react";

// Define types for FeatureCard props
interface FeatureCardProps {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  title: string;
  description: string;
}

// FeatureCard Component with types
const FeatureCard: React.FC<FeatureCardProps> = ({ icon: Icon, title, description }) => (
  <motion.div 
    whileHover={{ scale: 1.05 }}
    className="bg-white p-6 rounded-xl shadow-lg transform transition-transform"
  >
    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
      <Icon className="w-6 h-6 text-blue-600" />
    </div>
    <h3 className="text-xl font-semibold mb-2">{title}</h3>
    <p className="text-gray-600">{description}</p>
  </motion.div>
);


// Hero Section
const HeroSection = () => (
  <div className="relative bg-gradient-to-r from-blue-900 to-indigo-900 min-h-screen flex items-center">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-center"
      >
        {/* Logo */}
        <img
          src="/logo.jpg"
          alt="OpenSLAM Logo"
          className="mx-auto mb-6 w-520 h-520"
        />
        <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
        </h1>
        <p className="text-2xl text-blue-100 mb-8">
          Empowering researchers to build the future of autonomous systems
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <motion.button
            whileHover={{ scale: 1.1 }}
            className="px-8 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold transition-all"
          >
            Get Started
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.1 }}
            className="px-8 py-3 bg-transparent border-2 border-white text-white hover:bg-white hover:text-blue-900 rounded-lg font-semibold transition-all"
          >
            Learn More
          </motion.button>
        </div>
      </motion.div>
    </div>

    {/* Decorative Background */}
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <div className="absolute w-96 h-96 bg-blue-500 rounded-full opacity-20 blur-3xl -top-32 -left-32"></div>
      <div className="absolute w-96 h-96 bg-indigo-500 rounded-full opacity-20 blur-3xl -bottom-32 -right-32"></div>
    </div>
  </div>
);

// Features Section

// Features Section
const FeaturesSection = () => (
  <div className="py-20 bg-gray-50">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center mb-16">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">Platform Features</h2>
        <p className="text-xl text-gray-600">
          Explore tools to develop, visualize, and analyze SLAM algorithms.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <FeatureCard 
          icon={Code2}
          title="Algorithm Development"
          description="Build and test SLAM algorithms with our robust toolkit."
        />
        <FeatureCard 
          icon={Map}
          title="Real-time Visualization"
          description="Interactive 3D trajectory and point cloud visualizations."
        />
        <FeatureCard 
          icon={Share2}
          title="Seamless Integration"
          description="Integrate with datasets and SLAM frameworks effortlessly."
        />
        <FeatureCard 
          icon={Book}
          title="Educational Resources"
          description="Access tutorials and guides to master SLAM concepts."
        />
        <FeatureCard 
          icon={Users}
          title="Community Collaboration"
          description="Collaborate with researchers and developers worldwide."
        />
        <FeatureCard 
          icon={LineChart}
          title="Performance Insights"
          description="Analyze and benchmark SLAM algorithm performance."
        />
      </div>
    </div>
  </div>
);


// Testimonials Section
const TestimonialsSection = () => (
  <div className="py-20 bg-white">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center mb-16">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">What Our Users Say</h2>
        <p className="text-xl text-gray-600">Join thousands of researchers making a difference with OpenSLAM</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <motion.div 
          whileHover={{ y: -5 }}
          className="bg-gray-100 p-6 rounded-xl shadow-lg"
        >
          <p className="text-gray-600 mb-4">
            "OpenSLAM revolutionized the way I develop and test SLAM algorithms. It's intuitive and powerful!"
          </p>
          <h4 className="text-gray-900 font-semibold">- Dr. Jane Doe, Robotics Researcher</h4>
        </motion.div>
        <motion.div 
          whileHover={{ y: -5 }}
          className="bg-gray-100 p-6 rounded-xl shadow-lg"
        >
          <p className="text-gray-600 mb-4">
            "The visualization tools are incredible. Real-time insights have never been easier."
          </p>
          <h4 className="text-gray-900 font-semibold">- John Smith, Software Engineer</h4>
        </motion.div>
        <motion.div 
          whileHover={{ y: -5 }}
          className="bg-gray-100 p-6 rounded-xl shadow-lg"
        >
          <p className="text-gray-600 mb-4">
            "A must-have platform for any SLAM researcher. The community is also amazing!"
          </p>
          <h4 className="text-gray-900 font-semibold">- Emily Johnson, PhD Student</h4>
        </motion.div>
      </div>
    </div>
  </div>
);

// Call-to-Action Section
const CTASection = () => (
  <div className="py-20 bg-gradient-to-r from-indigo-900 to-blue-900 text-center text-white">
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <h2 className="text-4xl font-bold mb-6">Start Your SLAM Journey Today</h2>
      <p className="text-xl mb-8">
        Whether you're a beginner or an expert, OpenSLAM is your gateway to groundbreaking research.
      </p>
      <div className="flex flex-col sm:flex-row justify-center gap-4">
        <button className="px-8 py-3 bg-white text-blue-900 hover:bg-gray-100 rounded-lg font-semibold">
          Get Started for Free
        </button>
        <button className="flex items-center justify-center gap-2 px-8 py-3 bg-transparent border-2 border-white hover:bg-white hover:text-blue-900 rounded-lg font-semibold">
          <Github className="w-5 h-5" />
          View on GitHub
        </button>
      </div>
    </div>
  </div>
);

// Footer Section with GitHub Icon
const Footer = () => (
  <footer className="bg-gray-900 text-gray-300 py-12">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
          <h3 className="text-white font-semibold mb-4">OpenSLAM</h3>
          <p>Your open-source SLAM research companion.</p>
        </div>
        <div>
          <h4 className="text-white font-semibold mb-4">Resources</h4>
          <ul>
            <li className="hover:text-white">Documentation</li>
            <li className="hover:text-white">Community</li>
          </ul>
        </div>
        <div>
          <h4 className="text-white font-semibold mb-4">Stay Connected</h4>
          <ul>
            <li className="flex items-center gap-2 hover:text-white">
              <Github className="w-5 h-5" />
              GitHub
            </li>
          </ul>
        </div>
      </div>
      <p className="text-center text-sm mt-8">© {new Date().getFullYear()} OpenSLAM. All rights reserved.</p>
    </div>
  </footer>
);

export { FeaturesSection, Footer };
const LandingPage = () => {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <FeaturesSection />
      <TestimonialsSection />
      <CTASection />
      <Footer />
    </div>
  );
};

export default LandingPage;
