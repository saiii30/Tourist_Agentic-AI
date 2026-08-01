import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, Pagination } from "swiper/modules";
import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/pagination";

interface ImageSliderProps {
  images: string[];
}

export function ImageSlider({ images }: ImageSliderProps) {
  const swiperRef = useRef<any>(null);
  const showNav = images.length > 3;

  return (
    <div className="my-2 flex justify-center px-3">
      <div className="relative w-full max-w-[400px]">
        <Swiper
          modules={[Navigation, Pagination]}
          onSwiper={(swiper) => (swiperRef.current = swiper)}
          slidesPerView={3}
          spaceBetween={6}
          pagination={{ clickable: true }}
          loop={showNav}
        >
          {images.map((img, index) => (
            <SwiperSlide key={index}>
              <img src={img} alt={`Photo ${index + 1}`} className="h-24 w-full rounded-lg bg-slate-100 object-contain dark:bg-slate-900" loading="lazy" decoding="async" />
            </SwiperSlide>
          ))}
        </Swiper>

        {showNav && (
          <>
            <button
              onClick={() => swiperRef.current?.slidePrev()}
              aria-label="Previous"
              className="absolute left-0 top-1/2 z-10 flex h-6 w-6 -translate-x-2 -translate-y-1/2 items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-slate-300 shadow-md hover:bg-slate-700"
            >
              <ChevronLeft className="text-[9px]" />
            </button>
            <button
              onClick={() => swiperRef.current?.slideNext()}
              aria-label="Next"
              className="absolute right-0 top-1/2 z-10 flex h-6 w-6 translate-x-2 -translate-y-1/2 items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-slate-300 shadow-md hover:bg-slate-700"
            >
              <ChevronRight className="text-[9px]" />
            </button>
          </>
        )}
      </div>
    </div>
  );
}
