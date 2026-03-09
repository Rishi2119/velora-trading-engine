import Link from 'next/link';
import { useSupabaseClient, useUser } from '@supabase/auth-helpers-react';
import { useRouter } from 'next/navigation';

export default function NavBar() {
    const supabase = useSupabaseClient();
    const user = useUser();
    const router = useRouter();

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.refresh();
    };

    return (
        <nav className="bg-white dark:bg-gray-800 shadow p-4 flex justify-between items-center">
            <div className="flex space-x-4">
                <Link href="/" className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Velora
                </Link>
                {user && (
                    <Link href="/dashboard" className="text-gray-700 dark:text-gray-300 hover:underline">
                        Dashboard
                    </Link>
                )}
            </div>
            <div className="flex space-x-4">
                {user ? (
                    <button onClick={handleLogout} className="text-gray-700 dark:text-gray-300 hover:underline">
                        Logout
                    </button>
                ) : (
                    <>
                        <Link href="/login" className="text-gray-700 dark:text-gray-300 hover:underline">
                            Login
                        </Link>
                        <Link href="/signup" className="text-gray-700 dark:text-gray-300 hover:underline">
                            Sign Up
                        </Link>
                    </>
                )}
            </div>
        </nav>
    );
}
