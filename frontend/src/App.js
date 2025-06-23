import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Search, User, Lock, Clock, Tag, X, Mic, Heart, Briefcase, Paintbrush, Music, Tv } from 'lucide-react';

// --- Configuration ---
const API_BASE_URL = '/api';

// --- API Helper Functions ---
// In a real app, you might use a library like axios, but fetch is fine.
const api = {
  getAuctions: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auctions`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      // Assuming the API returns an array of auction objects or an object containing them
      const data = await response.json();
      
      // Check if data is an object with an 'auctions' property which is an array
      if (data && Array.isArray(data.auctions)) {
        return data.auctions;
      }
      
      // Check if data itself is an array
      if(Array.isArray(data) && data.length > 0) {
        return data;
      }

      // If API returns nothing useful, trigger fallback to mock data.
      console.warn("API returned no valid auction data. Using mock data.");
      return mockAuctions;

    } catch (error) {
      console.error("Could not fetch auctions:", error);
      console.warn("Falling back to mock data due to API error.");
      return mockAuctions; // Fallback to mock data on error
    }
  },
  // Placeholder for user login
  login: async (email, password) => {
    console.log("Attempting login for:", email);
    // In a real app, this would be:
    // const response = await fetch(`${API_BASE_URL}/api/auth/login`, { ... });
    // const { token, user } = await response.json();
    // return { token, user };
    return { token: 'fake-jwt-token', user: { name: 'Demo User', email } };
  },
  // Placeholder for user registration
  register: async (fullName, email, password) => {
    console.log("Attempting registration for:", fullName, email);
     // const response = await fetch(`${API_BASE_URL}/api/auth/register`, { ... });
     // const { token, user } = await response.json();
    return { token: 'fake-jwt-token', user: { name: fullName, email } };
  },
  // Placeholder for placing a bid
  placeBid: async (productId, amount, token) => {
      console.log(`Placing bid of ${amount} on product ${productId}`);
      // const response = await fetch(`${API_BASE_URL}/api/auctions/${productId}/bid`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      //   body: JSON.stringify({ amount })
      // });
      // if(!response.ok) throw new Error('Bid failed');
      // return await response.json();
      return { success: true, message: "Bid placed successfully!" };
  }
};

// --- Mock Data (as a fallback) ---
const mockAuctions = [
    { id: 1, name: 'Vintage Rolex Submariner', category: 'Watches', current_price: 15000, next_bid: 15500, bids: 23, end_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), image_url: 'https://images.unsplash.com/photo-1620625443224-b3695579455b?q=80&w=2864&auto=format&fit=crop', status: 'active' },
    { id: 2, name: 'Rare Pokémon Card Collection', category: 'Collectibles', current_price: 2500, next_bid: 2600, bids: 45, end_time: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(), image_url: 'https://images.unsplash.com/photo-1635832029474-1363593605ab?q=80&w=2864&auto=format&fit=crop', status: 'active' },
    { id: 3, name: 'Antique Chinese Vase', category: 'Art & Antiques', current_price: 8900, next_bid: 9000, bids: 12, end_time: new Date(Date.now() - 3600000).toISOString(), image_url: 'https://images.unsplash.com/photo-1579783928621-7a13d2687b43?q=80&w=2787&auto=format&fit=crop', status: 'ended' },
    { id: 4, name: 'Classic Gibson Guitar', category: 'Musical Instruments', current_price: 3200, next_bid: 3300, bids: 16, end_time: new Date(Date.now() + 1 * 60 * 60 * 1000).toISOString(), image_url: 'https://images.unsplash.com/photo-1550291652-6ea9114a47b1?q=80&w=2940&auto=format&fit=crop', status: 'active' },
    { id: 5, name: 'Luxury Handbag Collection', category: 'Fashion', current_price: 1200, next_bid: 1300, bids: 31, end_time: new Date(Date.now() + 15 * 60 * 1000).toISOString(), image_url: 'https://images.unsplash.com/photo-1590737149929-23a3c2292e92?q=80&w=2787&auto=format&fit=crop', status: 'ending_soon' },
    { id: 6, name: 'Vintage Camera Equipment', category: 'Electronics', current_price: 750, next_bid: 800, bids: 9, end_time: new Date(Date.now() + 5 * 60 * 60 * 1000).toISOString(), image_url: 'https://images.unsplash.com/photo-1512756290469-ec264b7fbf87?q=80&w=2856&auto=format&fit=crop', status: 'active' },
];

// --- Helper Components ---

const CountdownTimer = ({ endTime }) => {
  const calculateTimeLeft = useCallback(() => {
    const difference = +new Date(endTime) - +new Date();
    let timeLeft = {};

    if (difference > 0) {
      timeLeft = {
        days: Math.floor(difference / (1000 * 60 * 60 * 24)),
        hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
        minutes: Math.floor((difference / 1000 / 60) % 60),
        seconds: Math.floor((difference / 1000) % 60),
      };
    }

    return timeLeft;
  }, [endTime]);

  const [timeLeft, setTimeLeft] = useState(calculateTimeLeft());

  useEffect(() => {
    const timer = setTimeout(() => {
      setTimeLeft(calculateTimeLeft());
    }, 1000);

    return () => clearTimeout(timer);
  });
  
  const timerComponents = [];
  if (timeLeft.days > 0) timerComponents.push(`${timeLeft.days}d`);
  if (timeLeft.hours > 0 || timeLeft.days > 0) timerComponents.push(`${timeLeft.hours}h`);
  timerComponents.push(`${timeLeft.minutes}m`);
  timerComponents.push(`${timeLeft.seconds}s`);

  return (
    <div className="flex items-center space-x-1 text-sm text-gray-500">
        <Clock className="w-4 h-4" />
        <span>{Object.keys(timeLeft).length ? timerComponents.join(' ') : 'Auction Ended'}</span>
    </div>
  );
};

const AuthModal = ({ onClose, setAuthInfo }) => {
    const [isRegister, setIsRegister] = useState(false);
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (isRegister) {
            if (password !== confirmPassword) {
                setError("Passwords do not match");
                return;
            }
            try {
                const authData = await api.register(fullName, email, password);
                setAuthInfo(authData);
                onClose();
            } catch (err) {
                setError(err.message || "Registration failed");
            }
        } else {
            try {
                const authData = await api.login(email, password);
                setAuthInfo(authData);
                onClose();
            } catch (err) {
                setError(err.message || "Login failed");
            }
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-2xl p-8 w-full max-w-md relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
                    <X size={24} />
                </button>
                <h2 className="text-2xl font-bold text-center text-gray-800 mb-2">Welcome to BidHub</h2>
                <div className="flex justify-center mb-6">
                    <div className="bg-gray-100 p-1 rounded-lg flex space-x-1">
                        <button onClick={() => setIsRegister(false)} className={`px-6 py-2 rounded-md text-sm font-semibold ${!isRegister ? 'bg-white shadow' : 'text-gray-600'}`}>Sign In</button>
                        <button onClick={() => setIsRegister(true)} className={`px-6 py-2 rounded-md text-sm font-semibold ${isRegister ? 'bg-white shadow' : 'text-gray-600'}`}>Register</button>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>
                    <h3 className="text-xl font-semibold text-gray-700 mb-4 text-center">{isRegister ? 'Create Account' : 'Sign In'}</h3>
                    {error && <p className="text-red-500 text-sm mb-4 text-center">{error}</p>}
                    {isRegister && (
                        <div className="mb-4 relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                            <input type="text" placeholder="Enter your full name" value={fullName} onChange={e => setFullName(e.target.value)} className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400" required />
                        </div>
                    )}
                    <div className="mb-4 relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                        <input type="email" placeholder="Enter your email" value={email} onChange={e => setEmail(e.target.value)} className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400" required />
                    </div>
                    <div className="mb-4 relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                        <input type="password" placeholder="Create a password" value={password} onChange={e => setPassword(e.target.value)} className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400" required />
                    </div>
                     {isRegister && (
                        <div className="mb-6 relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                            <input type="password" placeholder="Confirm your password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400" required />
                        </div>
                    )}
                    <button type="submit" className="w-full bg-gray-800 text-white py-3 rounded-lg font-semibold hover:bg-gray-900 transition-colors">
                        {isRegister ? 'Create Account' : 'Sign In'}
                    </button>
                </form>
            </div>
        </div>
    );
};

const CategoryFilter = ({ selectedCategory, setSelectedCategory }) => {
    const categories = [
        { name: 'All', icon: Briefcase },
        { name: 'Watches', icon: Clock },
        { name: 'Collectibles', icon: Briefcase },
        { name: 'Art & Antiques', icon: Paintbrush },
        { name: 'Musical Instruments', icon: Music },
        { name: 'Fashion', icon: Tag },
        { name: 'Electronics', icon: Tv },
    ];

    return (
        <div className="flex items-center space-x-2 overflow-x-auto pb-2 -mx-4 px-4 sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
            {categories.map(({name, icon: Icon}) => (
                <button
                    key={name}
                    onClick={() => setSelectedCategory(name)}
                    className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-lg whitespace-nowrap transition-colors ${selectedCategory === name ? 'bg-indigo-600 text-white shadow' : 'bg-white text-gray-600 hover:bg-gray-100'}`}
                >
                  <Icon className="w-4 h-4"/>
                  <span>{name}</span>
                </button>
            ))}
        </div>
    );
};

const AuctionCard = ({ auction, onBidClick }) => {
    const { id, name, category, current_price, next_bid, bids, end_time, image_url, status } = auction;
    const isEnded = new Date(end_time) < new Date() || status === 'ended';
    
    let statusBadge;
    if (isEnded) {
        statusBadge = <div className="absolute top-3 left-3 bg-gray-700 text-white text-xs font-bold px-2 py-1 rounded-full">ENDED</div>;
    } else if (status === 'ending_soon') {
        statusBadge = <div className="absolute top-3 left-3 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full animate-pulse">ENDING SOON</div>;
    }

    return (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden transition-transform duration-300 hover:scale-105 group flex flex-col">
            <div className="relative">
                <div className="absolute top-3 left-3 bg-black bg-opacity-40 text-white text-xs font-bold px-2 py-1 rounded-full">{category}</div>
                {statusBadge}
                <button className="absolute top-3 right-3 bg-white/80 p-2 rounded-full text-gray-600 hover:text-red-500 hover:bg-white transition-all">
                    <Heart className="w-5 h-5"/>
                </button>
                <img src={image_url} alt={name} className="w-full h-56 object-cover" onError={(e) => { e.target.onerror = null; e.target.src=`https://placehold.co/600x400/e2e8f0/64748b?text=${name.replace(/\s/g,'+')}`}}/>
            </div>
            <div className="p-4 flex flex-col flex-grow">
                <h3 className="text-lg font-bold text-gray-800 truncate">{name}</h3>
                <div className="mt-4 flex justify-between items-center text-sm">
                    <div className="flex flex-col">
                        <span className="text-gray-500">Current Bid</span>
                        <span className="font-bold text-indigo-600 text-xl">${current_price.toLocaleString()}</span>
                    </div>
                    <div className="flex flex-col text-right">
                        <span className="text-gray-500">Next Bid</span>
                        <span className="font-bold text-gray-700 text-lg">${next_bid.toLocaleString()}</span>
                    </div>
                </div>
                <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center">
                    <span className="text-sm text-gray-500">{bids} bids</span>
                    <CountdownTimer endTime={end_time} />
                </div>
                 <div className="mt-auto pt-4">
                    <button 
                        onClick={() => onBidClick(auction)}
                        disabled={isEnded}
                        className={`w-full text-center font-semibold py-2.5 px-4 rounded-lg transition-all ${isEnded ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-300'}`}
                    >
                       {isEnded ? 'Auction Ended' : 'View & Bid'}
                    </button>
                </div>
            </div>
        </div>
    );
};

const Header = ({ onAuthClick, onHowItWorksClick, onAuctionsClick, authInfo, setAuthInfo }) => (
    <header className="bg-white/80 backdrop-blur-lg sticky top-0 z-40 shadow-sm">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
                <div className="flex-shrink-0">
                    <a href="/" onClick={(e) => { e.preventDefault(); onAuctionsClick(); }} className="text-2xl font-bold text-indigo-600">
                        BidHub
                    </a>
                </div>
                <nav className="hidden md:flex items-center space-x-8">
                    <a href="/" onClick={(e) => { e.preventDefault(); onAuctionsClick(); }} className="text-gray-600 hover:text-indigo-600 font-medium transition-colors">Auctions</a>
                    <a href="/" className="text-gray-600 hover:text-indigo-600 font-medium transition-colors">Categories</a>
                    <a href="/" onClick={(e) => { e.preventDefault(); onHowItWorksClick(); }} className="text-gray-600 hover:text-indigo-600 font-medium transition-colors">How It Works</a>
                </nav>
                <div className="flex items-center space-x-2">
                    {authInfo ? (
                        <div className="flex items-center space-x-3">
                            <span className="font-medium text-gray-700 hidden sm:block">Welcome, {authInfo.user.name.split(' ')[0]}</span>
                             <button onClick={() => setAuthInfo(null)} className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-600 bg-indigo-100 hover:bg-indigo-200">
                                Sign Out
                            </button>
                        </div>
                    ) : (
                        <>
                            <button onClick={() => onAuthClick('login')} className="hidden sm:block px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                                Sign In
                            </button>
                            <button onClick={() => onAuthClick('register')} className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                                Register
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    </header>
);

const AuctionsView = ({ auctions, onBidClick }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All');

    const filteredAuctions = useMemo(() => {
        return auctions
            .filter(auction => selectedCategory === 'All' || auction.category === selectedCategory)
            .filter(auction => auction.name.toLowerCase().includes(searchTerm.toLowerCase()));
    }, [auctions, selectedCategory, searchTerm]);

    const activeAuctions = filteredAuctions.filter(a => new Date(a.end_time) > new Date());
    
    return (
        <>
            {/* Hero Section */}
            <div className="bg-gradient-to-br from-indigo-600 to-purple-700 text-white">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
                    <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight">Premium Online Auctions</h1>
                    <p className="mt-4 text-lg md:text-xl max-w-2xl mx-auto text-indigo-100">Discover rare treasures and bid on exclusive items from around the world</p>
                    <button className="mt-8 px-8 py-3 bg-white text-indigo-600 font-semibold rounded-lg shadow-md hover:bg-gray-100 transition-transform hover:scale-105 flex items-center mx-auto space-x-2">
                        <Mic className="w-5 h-5"/>
                        <span>Live Auctions Now Active</span>
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="flex flex-col md:flex-row justify-between items-center gap-4 mb-8">
                    <div className="relative w-full md:max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                        <input
                            type="text"
                            placeholder="Search auctions..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400"
                        />
                    </div>
                    <CategoryFilter selectedCategory={selectedCategory} setSelectedCategory={setSelectedCategory} />
                </div>

                <div className="flex justify-between items-baseline mb-6">
                    <h2 className="text-3xl font-bold text-gray-800">Live Auctions ({activeAuctions.length})</h2>
                    <div className="text-sm font-medium text-gray-500">Ending Soon First</div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                    {filteredAuctions.map(auction => (
                        <AuctionCard key={auction.id} auction={auction} onBidClick={onBidClick} />
                    ))}
                </div>
            </main>
        </>
    );
};

const HowItWorksView = () => {
    const features = [
        { icon: User, title: '1. Register & Verify', description: 'Create your account, verify your identity, and set up your bidding preferences. Our secure platform ensures your information is protected.' },
        { icon: Search, title: '2. Browse Live Auctions', description: 'Explore our curated selection of auction items. Filter by category, price range, or time remaining to find items that interest you.' },
        { icon: Mic, title: '3. Place Bids (Voice or Manual)', description: 'Use our innovative voice assistant to place bids hands-free, or use the traditional web interface. Both methods provide real-time feedback and confirmation.' },
        { icon: Briefcase, title: '4. Win & Collect', description: 'When you win an auction, you\'ll receive instant notification. Complete the payment process and arrange for secure delivery of your item.' }
    ];

    const keyFeatures = [
        { icon: Clock, title: 'Real-Time Updates', description: 'Live bid tracking with instant notifications and WebSocket connections.' },
        { icon: Mic, title: 'Voice Bidding', description: 'Revolutionary AI-powered voice assistant for hands-free bidding.' },
        { icon: Lock, title: 'Secure Platform', description: 'Advanced security measures to protect your data and transactions.' }
    ];

    return (
        <div className="bg-white">
            <div className="bg-gradient-to-br from-indigo-600 to-purple-700 text-white">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
                    <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">How BidHub Works</h1>
                    <p className="mt-4 text-lg md:text-xl max-w-3xl mx-auto text-indigo-100">Experience the future of online auctions with AI-powered voice bidding</p>
                </div>
            </div>

            <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16">
                <div className="max-w-4xl mx-auto">
                    <div className="bg-gray-50 p-8 rounded-xl shadow-sm">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4">About BidHub</h2>
                        <p className="text-gray-600 leading-relaxed">
                            BidHub is a revolutionary online bidding platform that combines traditional auction functionality with cutting-edge AI voice assistant technology. Our platform allows users to participate in real-time auctions using both traditional web interfaces and innovative voice commands.
                        </p>
                        <p className="text-gray-600 leading-relaxed mt-4">
                            Built with modern web technologies including React, WebSocket connections for real-time updates, and integrated voice recognition, BidHub provides a seamless and engaging auction experience for both casual bidders and serious collectors.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8 my-12">
                        {features.map(feature => (
                            <div key={feature.title} className="bg-white p-6 border border-gray-200 rounded-lg">
                                <div className="flex items-center space-x-4">
                                    <div className="bg-indigo-100 p-3 rounded-full">
                                        <feature.icon className="w-6 h-6 text-indigo-600" />
                                    </div>
                                    <h3 className="text-lg font-semibold text-gray-800">{feature.title}</h3>
                                </div>
                                <p className="mt-3 text-gray-600">{feature.description}</p>
                            </div>
                        ))}
                    </div>

                    <div className="text-center">
                        <h2 className="text-3xl font-bold text-gray-800 mb-8">Key Features</h2>
                         <div className="grid md:grid-cols-3 gap-8">
                             {keyFeatures.map(feature => (
                                <div key={feature.title} className="text-center">
                                    <div className="flex justify-center mb-4">
                                        <div className="bg-indigo-100 p-4 rounded-full">
                                            <feature.icon className="w-8 h-8 text-indigo-600" />
                                        </div>
                                    </div>
                                    <h3 className="text-xl font-semibold text-gray-800">{feature.title}</h3>
                                    <p className="mt-2 text-gray-600">{feature.description}</p>
                                </div>
                             ))}
                         </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// --- Main App Component ---
export default function App() {
    const [auctions, setAuctions] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
    const [authInfo, setAuthInfo] = useState(null); // { token, user }
    const [currentView, setCurrentView] = useState('auctions'); // 'auctions' or 'howitworks'

    useEffect(() => {
        const fetchAuctions = async () => {
            try {
                setIsLoading(true);
                const data = await api.getAuctions();
                
                // Ensure we have a valid array before trying to sort it
                if (Array.isArray(data)) {
                    // Sort by end time, soonest first, but keep ended ones at the bottom
                    data.sort((a, b) => {
                        const aEnded = new Date(a.end_time) < new Date();
                        const bEnded = new Date(b.end_time) < new Date();
                        if (aEnded && !bEnded) return 1;
                        if (!aEnded && bEnded) return -1;
                        return new Date(a.end_time) - new Date(b.end_time);
                    });
                    setAuctions(data);
                } else {
                    // If data is not an array (e.g., from fallback), just set it
                    setAuctions(mockAuctions); // Fallback to a known good array
                }

                setError(null);
            } catch (err) {
                setError(err.message);
                setAuctions(mockAuctions); // Use mock data on error
            } finally {
                setIsLoading(false);
            }
        };

        fetchAuctions();
        
        // Optional: Set up polling to refresh auction data periodically
        const intervalId = setInterval(fetchAuctions, 60000); // every 60 seconds
        return () => clearInterval(intervalId);

    }, []);

    const handleAuthClick = (type) => { // type can be 'login' or 'register'
        setIsAuthModalOpen(true);
    };

    const handleBidClick = (auction) => {
        // Prevent bidding if not logged in
        if (!authInfo) {
            alert('Please sign in to place a bid.');
            setIsAuthModalOpen(true);
            return;
        }
        // This would open a dedicated bidding modal/view
        alert(`Bidding on: ${auction.name}`);
    };
    
    const renderView = () => {
        switch (currentView) {
            case 'auctions':
                if (isLoading) return <div className="flex justify-center items-center h-screen"><p className="text-lg">Loading auctions...</p></div>;
                if (error) return <div className="flex justify-center items-center h-screen"><p className="text-lg text-red-500">Error: {error}</p></div>;
                return <AuctionsView auctions={auctions} onBidClick={handleBidClick} />;
            case 'howitworks':
                return <HowItWorksView />;
            default:
                return <AuctionsView auctions={auctions} onBidClick={handleBidClick} />;
        }
    };

    return (
        <div className="bg-gray-50 min-h-screen font-sans">
            <Header 
                onAuthClick={handleAuthClick} 
                onHowItWorksClick={() => setCurrentView('howitworks')}
                onAuctionsClick={() => setCurrentView('auctions')}
                authInfo={authInfo}
                setAuthInfo={setAuthInfo}
            />
            {renderView()}

            {isAuthModalOpen && <AuthModal onClose={() => setIsAuthModalOpen(false)} setAuthInfo={setAuthInfo} />}
            
            <footer className="bg-gray-800 text-white">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center">
                    <p>&copy; 2025 BidHub. All rights reserved.</p>
                    <p className="text-sm text-gray-400 mt-2">The future of online auctions, powered by AI.</p>
                </div>
            </footer>
        </div>
    );
}
